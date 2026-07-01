from pathlib import Path

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

        section[data-testid="stSidebar"] {{
            background-color: {PRIMARY};
        }}

        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}

        div[data-baseweb="select"] * {{
            color: #111827 !important;
        }}

        .stSelectbox label,
        .stFileUploader label {{
            color: white !important;
            font-size: 13px !important;
        }}

        .block-container {{
            max-width: 1120px;
            padding-top: 0.9rem;
            padding-bottom: 2rem;
        }}

        h1 {{
            font-size: 26px !important;
            line-height: 1.1 !important;
        }}

        h2 {{
            font-size: 19px !important;
            margin-top: 0.75rem !important;
            margin-bottom: 0.45rem !important;
        }}

        h3 {{
            font-size: 16px !important;
        }}

        .hero {{
            background: {PRIMARY};
            color: white;
            padding: 12px 18px;
            border-radius: 14px;
            margin-bottom: 12px;
        }}

        .hero h1 {{
            color: white !important;
            font-size: 24px !important;
            margin-bottom: 3px;
        }}

        .hero p {{
            color: white !important;
            margin: 0;
            font-size: 13px;
        }}

        div[data-testid="stVerticalBlock"] {{
            gap: 0.55rem;
        }}

        div[data-testid="stExpander"] {{
            background: white;
            border-radius: 12px;
        }}

        .stButton button,
        .stLinkButton a {{
            background-color: {PRIMARY} !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.35rem 0.75rem !important;
            font-size: 13px !important;
            font-weight: 650 !important;
            border: 0 !important;
        }}

        [data-testid="stMetric"] {{
            background: white;
            border: 1px solid #E6E8EF;
            border-radius: 12px;
            padding: 12px 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }}

        [data-testid="stMetricValue"] {{
            font-size: 24px !important;
            color: {PRIMARY};
        }}

        [data-testid="stMetricLabel"] {{
            font-size: 12px !important;
            color: #6B7280 !important;
        }}

        div[data-testid="stContainer"] {{
            border-radius: 12px !important;
        }}

        .element-container {{
            margin-bottom: 0.25rem !important;
        }}

        p {{
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
def read_plan_from_path(file_path: str):
    excel = pd.ExcelFile(file_path)
    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in excel.sheet_names]
    if missing:
        raise ValueError("Missing sheets: " + ", ".join(missing))
    return {sheet: normalize_columns(pd.read_excel(file_path, sheet_name=sheet)) for sheet in REQUIRED_SHEETS}


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
            st.markdown(f"**{clean(row.get('Arbejdsopgave'), 'Task')}**")
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

    priority_icon = {
        "Kritisk": "🔴",
        "Høj": "🟠",
        "Normal": "🟡",
        "Lav": "🟢",
    }.get(priority, "⚪")

    meta = " · ".join([x for x in [
        " / ".join([x for x in [system, workspace] if x]),
        banner,
        frequency,
        f"{minutes} min" if minutes else "",
    ] if x])

    with st.container(border=True):
        top_left, top_right = st.columns([5, 1])
        with top_left:
            st.markdown(f"### {title}")
        with top_right:
            if label:
                st.markdown(f"**{priority_icon} {label}**")

        if meta:
            st.caption(f"📍 {meta}")

        if takeover:
            st.info(f"Taken over from {takeover}")

        if description:
            st.markdown(
                f"<div style='font-size:14px; color:#4B5563; margin-top:8px;'>{description}</div>",
                unsafe_allow_html=True,
            )

        if link:
            button_label = f"Open {system}" if system else "Open Workspace"
            st.link_button(button_label, link)

def render_tasks(title, df):
    if df is None or df.empty:
        return

    st.markdown(f"## {title}")

    for _, row in sort_tasks(df).iterrows():
        task_card(row)



def render_my_tasks(assignments, person):
    person_tasks = tasks_for_person(assignments, person)
    staffing = requires_staffing(assignments)

    taken_over = pd.DataFrame()
    if not person_tasks.empty and "Taken Over From" in person_tasks.columns:
        taken_over = person_tasks[person_tasks["Taken Over From"].apply(clean) != ""].copy()

    if person_tasks.empty and staffing.empty:
        st.info("No tasks found.")
        return

    critical = person_tasks[person_tasks["Prioritet"].astype(str).str.strip().eq("Kritisk")] if "Prioritet" in person_tasks.columns else pd.DataFrame()
    high = person_tasks[person_tasks["Prioritet"].astype(str).str.strip().eq("Høj")] if "Prioritet" in person_tasks.columns else pd.DataFrame()

    daily = person_tasks[
        person_tasks["Frekvens"].astype(str).str.strip().eq("Daglig")
        & ~person_tasks["Prioritet"].astype(str).str.strip().isin(["Kritisk", "Høj"])
    ] if "Frekvens" in person_tasks.columns and "Prioritet" in person_tasks.columns else pd.DataFrame()

    weekly = person_tasks[
        person_tasks["Frekvens"].astype(str).str.strip().eq("Ugentlig")
        & ~person_tasks["Prioritet"].astype(str).str.strip().isin(["Kritisk", "Høj"])
    ] if "Frekvens" in person_tasks.columns and "Prioritet" in person_tasks.columns else pd.DataFrame()

    monthly = person_tasks[
        person_tasks["Frekvens"].astype(str).str.strip().eq("Månedlig")
        & ~person_tasks["Prioritet"].astype(str).str.strip().isin(["Kritisk", "Høj"])
    ] if "Frekvens" in person_tasks.columns and "Prioritet" in person_tasks.columns else pd.DataFrame()

    render_tasks("🔴 Critical", critical)
    render_tasks("🟠 High", high)
    render_tasks("📅 Daily", daily)
    render_tasks("📆 Weekly", weekly)
    render_tasks("🗓 Monthly", monthly)
    render_tasks("🔄 Taken over", taken_over)
    render_tasks("🚨 Requires Staffing", staffing)


def render_dashboard(assignments, availability, week, projects):
    staffing = requires_staffing(assignments)
    takeovers = takeover_tasks(assignments)
    availability_summary = team_availability_summary(availability, week)
    unavailable = availability_summary[availability_summary["Available"] == False] if not availability_summary.empty else pd.DataFrame()

    active_projects = pd.DataFrame()
    if projects is not None and not projects.empty:
        project_week = projects["Uge"].astype(str).str.strip() if "Uge" in projects.columns else ""
        active_projects = projects[project_week.eq(str(week).strip())].copy() if "Uge" in projects.columns else projects.copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requires Staffing", len(staffing))
    c2.metric("Taken over tasks", len(takeovers))
    c3.metric("Unavailable people", len(unavailable))
    c4.metric("Active project tasks", len(active_projects))

    st.markdown("## Overview")
    overview_rows = []
    if not unavailable.empty:
        for _, row in unavailable.iterrows():
            overview_rows.append({
                "Type": "Unavailable",
                "Person": row.get("Navn", ""),
                "Detail": row.get("Status", ""),
            })
    if not takeovers.empty:
        for _, row in takeovers.iterrows():
            overview_rows.append({
                "Type": "Taken over",
                "Person": row.get("Assigned To", ""),
                "Detail": f"{row.get('Arbejdsopgave', '')} from {row.get('Taken Over From', '')}",
            })
    if overview_rows:
        st.dataframe(pd.DataFrame(overview_rows), use_container_width=True, hide_index=True)
    else:
        st.success("No availability or takeover issues found for this week.")

    render_tasks("🚨 Requires Staffing", staffing)

    if not takeovers.empty:
        st.markdown("## 🔄 Taken over tasks")
        cols = ["Arbejdsopgave", "Assigned To", "Taken Over From", "Frekvens", "Prioritet"]
        existing = [c for c in cols if c in takeovers.columns]
        st.dataframe(takeovers[existing], use_container_width=True, hide_index=True)

    if not active_projects.empty:
        st.markdown("## 📌 Active project tasks")
        st.dataframe(active_projects, use_container_width=True, hide_index=True)


def main():
    st.set_page_config(page_title="PE Planner", page_icon="📋", layout="wide")
    inject_css()

    plan_path = Path("sample_data/current_plan.xlsx")

    with st.sidebar:
        st.markdown("# PE Planner")
        if plan_path.exists():
            st.success("Active plan loaded")
            st.caption("sample_data/current_plan.xlsx")
        else:
            st.error("No active plan found")

    if not plan_path.exists():
        hero("PE Planner", "No active plan found.")
        st.info("Add the active Excel file to GitHub as: sample_data/current_plan.xlsx")
        return

    try:
        data = read_plan_from_path(str(plan_path))
    except Exception as exc:
        hero("Import failed", "The active plan could not be read.")
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
        render_my_tasks(assignments, person)

    elif page == "Dashboard":
        render_dashboard(assignments, availability, week, projects)

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
        st.write("**Version:** Pilot Polish")
        st.write("**Plan source:** sample_data/current_plan.xlsx")
        st.write("The plan is maintained by the administrator. Team members only need to open the app link.")
        st.write(f"Employees: {len(team)}")
        st.write(f"Recurring tasks: {len(tasks)}")
        st.write(f"Projects / ad hoc rows: {len(projects)}")


if __name__ == "__main__":
    main()
