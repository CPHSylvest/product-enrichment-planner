import pandas as pd
import streamlit as st

from services.excel_service import (
    build_assignments,
    clean,
    get_available_weeks,
    requires_staffing,
    start_day_tasks,
    tasks_for_person,
    team_availability_summary,
    takeover_tasks,
)

PRIMARY = "#000066"
BG = "#F5F6FA"

REQUIRED_SHEETS = [
    "Team",
    "Arbejdsopgaver",
    "Workspaces",
    "Tilgængelighed",
    "Plan & Projekter",
]

PRIORITY_LABELS = {
    "Kritisk": "Critical",
    "Høj": "High",
    "Normal": "Normal",
    "Lav": "Low",
}

PRIORITY_ORDER = {
    "Kritisk": 1,
    "Høj": 2,
    "Normal": 3,
    "Lav": 4,
}


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {BG}; }}
        section[data-testid="stSidebar"] {{ background-color: {PRIMARY}; }}
        section[data-testid="stSidebar"] * {{ color: white !important; }}
        div[data-baseweb="select"] * {{ color: #111827 !important; }}
        .stSelectbox label, .stFileUploader label {{ color: white !important; }}
        .block-container {{ max-width: 1120px; padding-top: 1.25rem; }}
        h1 {{ font-size: 30px !important; }}
        h2 {{ font-size: 22px !important; margin-top: 1rem !important; }}
        h3 {{ font-size: 18px !important; }}
        .hero {{
            background: {PRIMARY};
            color: white;
            padding: 18px 24px;
            border-radius: 18px;
            margin-bottom: 18px;
        }}
        .hero h1 {{
            color: white !important;
            font-size: 28px !important;
            margin-bottom: 6px;
        }}
        .hero p {{
            color: white !important;
            margin: 0;
            font-size: 14px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_columns(df):
    df = df.copy()
    df.columns = [clean(c) for c in df.columns]
    return df


@st.cache_data(show_spinner=False)
def read_plan(uploaded_file):
    excel = pd.ExcelFile(uploaded_file)
    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in excel.sheet_names]
    if missing:
        raise ValueError("Missing sheets: " + ", ".join(missing))
    return {sheet: normalize_columns(pd.read_excel(uploaded_file, sheet_name=sheet)) for sheet in REQUIRED_SHEETS}


def active_rows(df):
    if df is None or df.empty:
        return pd.DataFrame()
    if "Aktiv" not in df.columns:
        return df.copy()
    active = df["Aktiv"].fillna("Ja").astype(str).str.strip().str.lower()
    return df[active.isin(["ja", "yes", "1", "true"])].copy()


def workspace_map(workspaces):
    mapping = {}
    for _, row in active_rows(workspaces).iterrows():
        system = clean(row.get("System"))
        workspace = clean(row.get("Workspace"))
        link = clean(row.get("Link"))
        if system or workspace:
            mapping[(system, workspace)] = link
    return mapping


def add_workspace_links(df, workspaces):
    if df is None or df.empty:
        return pd.DataFrame()
    result = df.copy()
    links = workspace_map(workspaces)
    result["__link"] = result.apply(
        lambda r: links.get((clean(r.get("System")), clean(r.get("Workspace"))), ""),
        axis=1,
    )
    return result


def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{clean(title)}</h1>
            <p>{clean(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sort_tasks(df):
    if df is None or df.empty:
        return pd.DataFrame()
    result = df.copy()
    result["__priority_sort"] = result["Prioritet"].map(PRIORITY_ORDER).fillna(99)
    return result.sort_values(["__priority_sort", "Frekvens", "Arbejdsopgave"])


def task_card(row):
    if bool(row.get("Requires Staffing", False)):
        with st.container(border=True):
            st.error("🚨 Requires Staffing")
            st.subheader(clean(row.get("Arbejdsopgave"), "Task"))
            reason = clean(row.get("Staffing Reason"))
            if reason:
                st.caption(reason)
        return

    title = clean(row.get("Arbejdsopgave"), "Untitled task")
    priority = clean(row.get("Prioritet"))
    label = PRIORITY_LABELS.get(priority, priority)
    system = clean(row.get("System"))
    workspace = clean(row.get("Workspace"))
    banner = clean(row.get("Banner"))
    frequency = clean(row.get("Frekvens"))
    minutes = clean(row.get("Estimeret tid")) or clean(row.get("Estimeret tid (min)"))
    description = clean(row.get("Beskrivelse"))
    takeover = clean(row.get("Taken Over From"))
    link = clean(row.get("__link"))

    meta = " · ".join([x for x in [
        " / ".join([x for x in [system, workspace] if x]),
        banner,
        frequency,
        f"{minutes} min" if minutes else "",
    ] if x])

    with st.container(border=True):
        if label:
            st.caption(label)
        st.subheader(title)
        if meta:
            st.caption(meta)
        if takeover:
            st.info(f"Taken over from {takeover}")
        if description:
            st.write(description)
        if link:
            button_label = f"Open {system}" if system else "Open Workspace"
            st.link_button(button_label, link)


def render_tasks(title, df):
    st.markdown(f"## {title}")
    if df is None or df.empty:
        st.info("No tasks found.")
        return
    for _, row in sort_tasks(df).iterrows():
        task_card(row)


def render_dashboard(assignments, availability, week):
    staffing = requires_staffing(assignments)
    takeovers = takeover_tasks(assignments)
    availability_summary = team_availability_summary(availability, week)
    unavailable = availability_summary[availability_summary["Available"] == False] if not availability_summary.empty else pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    c1.metric("Requires Staffing", len(staffing))
    c2.metric("Taken over tasks", len(takeovers))
    c3.metric("Unavailable people", len(unavailable))

    render_tasks("Requires Staffing", staffing)

    if not takeovers.empty:
        st.markdown("## Taken over tasks")
        st.dataframe(
            takeovers[["Arbejdsopgave", "Assigned To", "Taken Over From", "Frekvens", "Prioritet"]],
            use_container_width=True,
            hide_index=True,
        )


def main():
    st.set_page_config(page_title="PE Planner", page_icon="📋", layout="wide")
    inject_css()

    with st.sidebar:
        st.markdown("# PE Planner")
        uploaded = st.file_uploader("Import Plan", type=["xlsx"])

    if not uploaded:
        hero("PE Planner", "Import PE Planner Administration to start.")
        st.info("Use the sidebar to import your PE Planner Administration Excel file.")
        return

    try:
        data = read_plan(uploaded)
    except Exception as exc:
        hero("Import failed", "The Excel file could not be read.")
        st.error(str(exc))
        return

    team = active_rows(data["Team"])
    tasks = active_rows(data["Arbejdsopgaver"])
    workspaces = active_rows(data["Workspaces"])
    availability = data["Tilgængelighed"]
    projects = data["Plan & Projekter"]

    weeks = get_available_weeks(availability)
    people = team["Navn"].dropna().astype(str).tolist() if "Navn" in team.columns else []

    with st.sidebar:
        week = st.selectbox("Week", weeks, index=0 if weeks else None)
        person = st.selectbox("Person", people, index=0 if people else None)
        page = st.radio("Navigation", ["Start Day", "My Tasks", "Dashboard", "Team", "Projects", "About"])

    if not person or not week:
        st.warning("Please select a week and a person.")
        return

    assignments = build_assignments(tasks, availability, week)
    assignments = add_workspace_links(assignments, workspaces)

    hero(f"Good morning {person} 👋", f"{week}")

    if page == "Start Day":
        render_tasks("Start Day", start_day_tasks(assignments, person))

    elif page == "My Tasks":
        person_tasks = tasks_for_person(assignments, person)
        render_tasks("Daily", person_tasks[person_tasks["Frekvens"].astype(str).str.strip().eq("Daglig")])
        render_tasks("Weekly", person_tasks[person_tasks["Frekvens"].astype(str).str.strip().eq("Ugentlig")])
        render_tasks("Monthly", person_tasks[person_tasks["Frekvens"].astype(str).str.strip().eq("Månedlig")])

    elif page == "Dashboard":
        render_dashboard(assignments, availability, week)

    elif page == "Team":
        st.markdown("## Team")
        st.dataframe(team, use_container_width=True, hide_index=True)
        st.markdown("## Availability")
        st.dataframe(team_availability_summary(availability, week), use_container_width=True, hide_index=True)

    elif page == "Projects":
        st.markdown("## Projects")
        st.dataframe(projects, use_container_width=True, hide_index=True)

    elif page == "About":
        st.markdown("## About PE Planner")
        st.write("Version: Sprint 5 UI fix")
        st.write(f"Employees: {len(team)}")
        st.write(f"Recurring tasks: {len(tasks)}")
        st.write(f"Projects / ad hoc rows: {len(projects)}")


if __name__ == "__main__":
    main()
