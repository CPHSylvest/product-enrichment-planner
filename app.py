import html
from typing import Any

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
NAVY = "#000033"
BG = "#F5F6FA"
CARD = "#FFFFFF"
TEXT = "#252A36"
MUTED = "#6B7280"

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

PRIORITY_CLASS = {
    "Kritisk": "critical",
    "Høj": "high",
    "Normal": "normal",
    "Lav": "low",
}


def esc(value: Any) -> str:
    return html.escape(clean(value))


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {BG}; }}
        section[data-testid="stSidebar"] {{ background-color: {PRIMARY}; }}
        section[data-testid="stSidebar"] * {{ color: white !important; }}
        div[data-baseweb="select"] * {{ color: #111827 !important; }}
        .stSelectbox label, .stFileUploader label {{ color: white !important; }}
        .block-container {{ max-width: 1180px; padding-top: 1.5rem; padding-bottom: 2.5rem; }}
        h1 {{ font-size: 30px !important; line-height: 1.1 !important; color: {TEXT}; }}
        h2 {{ font-size: 22px !important; color: {TEXT}; margin-top: 1.0rem !important; }}
        h3 {{ font-size: 18px !important; color: {TEXT}; }}

        .hero {{
            background: {PRIMARY};
            color: white;
            padding: 18px 24px;
            border-radius: 18px;
            margin-bottom: 18px;
        }}
        .hero h1 {{ color: white !important; font-size: 28px !important; margin: 0 0 6px 0; }}
        .hero p {{ color: white !important; font-size: 14px; margin: 0; }}

        .task-card {{
            background: {CARD};
            border: 1px solid #E6E8EF;
            border-radius: 14px;
            padding: 13px 16px;
            margin-bottom: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,.04);
        }}
        .task-title {{ font-size: 18px; font-weight: 750; color: {TEXT}; margin: 2px 0 4px 0; }}
        .task-meta {{ font-size: 13px; color: {MUTED}; margin-bottom: 4px; }}
        .task-desc {{ font-size: 13px; color: #7A7F8C; margin: 6px 0 8px 0; }}
        .pill {{ display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; margin-bottom: 5px; }}
        .critical {{ background: #FDE2E2; color: #A60000; }}
        .high {{ background: #FFE8CC; color: #A64B00; }}
        .normal {{ background: #FFF3BF; color: #7A5A00; }}
        .low {{ background: #DFF5E1; color: #1E6B2D; }}
        .staffing {{ background: #A60000; color: white; }}

        .workspace-button {{
            display: inline-block;
            background: {PRIMARY};
            color: white !important;
            text-decoration: none;
            padding: 7px 12px;
            border-radius: 9px;
            font-size: 13px;
            font-weight: 750;
        }}
        .muted {{ color: {MUTED}; font-size: 13px; }}
        .empty {{ background: white; border: 1px dashed #D1D5DB; padding: 14px; border-radius: 12px; color: {MUTED}; }}

        .alert-card {{
            background: #FFF1F1;
            border: 1px solid #FFB4B4;
            border-left: 6px solid #A60000;
            border-radius: 14px;
            padding: 13px 16px;
            margin-bottom: 10px;
        }}
        .alert-title {{ font-size: 17px; font-weight: 800; color: #A60000; margin-bottom: 4px; }}

        .kpi {{
            background: white;
            border: 1px solid #E6E8EF;
            border-radius: 14px;
            padding: 14px;
            margin-bottom: 10px;
        }}
        .kpi-value {{ font-size: 28px; font-weight: 850; color: {PRIMARY}; }}
        .kpi-label {{ font-size: 13px; color: {MUTED}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [clean(c) for c in df.columns]
    return df


@st.cache_data(show_spinner=False)
def read_plan(uploaded_file) -> dict[str, pd.DataFrame]:
    excel = pd.ExcelFile(uploaded_file)
    missing = [sheet for sheet in REQUIRED_SHEETS if sheet not in excel.sheet_names]
    if missing:
        raise ValueError("Missing sheets: " + ", ".join(missing))
    return {sheet: normalize_columns(pd.read_excel(uploaded_file, sheet_name=sheet)) for sheet in REQUIRED_SHEETS}


def active_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if "Aktiv" not in df.columns:
        return df.copy()
    return df[df["Aktiv"].fillna("Ja").astype(str).str.strip().str.lower().isin(["ja", "yes", "1", "true"])].copy()


def workspace_map(workspaces: pd.DataFrame) -> dict[tuple[str, str], str]:
    mapping = {}
    for _, row in active_rows(workspaces).iterrows():
        system = clean(row.get("System"))
        workspace = clean(row.get("Workspace"))
        link = clean(row.get("Link"))
        if system or workspace:
            mapping[(system, workspace)] = link
    return mapping


def add_workspace_links(df: pd.DataFrame, workspaces: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    result = df.copy()
    links = workspace_map(workspaces)
    result["__link"] = result.apply(
        lambda r: links.get((clean(r.get("System")), clean(r.get("Workspace"))), ""),
        axis=1,
    )
    return result


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def staffing_card(row: pd.Series) -> None:
    title = clean(row.get("Arbejdsopgave"), "Task")
    reason = clean(row.get("Staffing Reason"))
    st.markdown(
        f"""
        <div class="alert-card">
            <div class="alert-title">🚨 Requires Staffing</div>
            <div class="task-title">{esc(title)}</div>
            <div class="task-meta">{esc(reason)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def task_card(row: pd.Series) -> None:
    if bool(row.get("Requires Staffing", False)):
        staffing_card(row)
        return

    title = clean(row.get("Arbejdsopgave"), "Untitled task")
    priority = clean(row.get("Prioritet"))
    label = PRIORITY_LABELS.get(priority, priority)
    css_class = PRIORITY_CLASS.get(priority, "normal")
    system = clean(row.get("System"))
    workspace = clean(row.get("Workspace"))
    banner = clean(row.get("Banner"))
    frequency = clean(row.get("Frekvens"))
    minutes = clean(row.get("Estimeret tid")) or clean(row.get("Estimeret tid (min)"))
    desc = clean(row.get("Beskrivelse"))
    takeover = clean(row.get("Taken Over From"))
    link = clean(row.get("__link"))

    meta_parts = []
    if system or workspace:
        meta_parts.append(" / ".join([p for p in [system, workspace] if p]))
    if banner:
        meta_parts.append(banner)
    if frequency:
        meta_parts.append(frequency)
    if minutes:
        meta_parts.append(f"{minutes} min")
    meta = " · ".join(meta_parts)

    takeover_html = f'<div class="task-desc"><b>Taken over from {esc(takeover)}</b></div>' if takeover else ""
    desc_html = f'<div class="task-desc">{esc(desc)}</div>' if desc else ""
    button_label = f"Open {system}" if system else "Open Workspace"
    link_html = f'<a class="workspace-button" href="{esc(link)}" target="_blank">{esc(button_label)}</a>' if link else '<div class="muted">No direct workspace link</div>'
    pill_html = f'<span class="pill {css_class}">{esc(label)}</span>' if label else ""

    st.markdown(
        f"""
        <div class="task-card">
            {pill_html}
            <div class="task-title">{esc(title)}</div>
            <div class="task-meta">{esc(meta)}</div>
            {takeover_html}
            {desc_html}
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tasks(title: str, df: pd.DataFrame) -> None:
    st.markdown(f"## {esc(title)}")
    if df is None or df.empty:
        st.markdown('<div class="empty">No tasks found.</div>', unsafe_allow_html=True)
        return
    for _, row in df.iterrows():
        task_card(row)


def render_dashboard(assignments: pd.DataFrame, availability: pd.DataFrame, week: str) -> None:
    staffing = requires_staffing(assignments)
    takeovers = takeover_tasks(assignments)
    availability_summary = team_availability_summary(availability, week)
    unavailable = availability_summary[availability_summary["Available"] == False] if not availability_summary.empty else pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="kpi"><div class="kpi-value">{len(staffing)}</div><div class="kpi-label">Requires Staffing</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi"><div class="kpi-value">{len(takeovers)}</div><div class="kpi-label">Taken over tasks</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi"><div class="kpi-value">{len(unavailable)}</div><div class="kpi-label">Unavailable people</div></div>', unsafe_allow_html=True)

    render_tasks("Requires Staffing", staffing)
    if not takeovers.empty:
        st.markdown("## Taken over tasks")
        st.dataframe(takeovers[["Arbejdsopgave", "Assigned To", "Taken Over From", "Frekvens", "Prioritet"]], use_container_width=True, hide_index=True)


def main() -> None:
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
        render_tasks("Daily", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Daglig")])
        render_tasks("Weekly", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Ugentlig")])
        render_tasks("Monthly", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Månedlig")])
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
        st.write("Version: Sprint 5 - Assignment Engine")
        st.write(f"Employees: {len(team)}")
        st.write(f"Recurring tasks: {len(tasks)}")
        st.write(f"Projects / ad hoc rows: {len(projects)}")


if __name__ == "__main__":
    main()
