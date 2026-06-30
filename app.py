import html
from typing import Any

import pandas as pd
import streamlit as st

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

PRIORITY_ORDER = {
    "Kritisk": 1,
    "Høj": 2,
    "Normal": 3,
    "Lav": 4,
}

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


def clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return default
    return text


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
        .block-container {{ max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }}
        h1 {{ font-size: 34px !important; line-height: 1.1 !important; color: {TEXT}; }}
        h2 {{ font-size: 24px !important; color: {TEXT}; margin-top: 1.2rem !important; }}
        h3 {{ font-size: 19px !important; color: {TEXT}; }}
        .hero {{
            background: {PRIMARY}; color: white; padding: 28px 34px;
            border-radius: 22px; margin-bottom: 24px;
        }}
        .hero h1 {{ color: white !important; font-size: 34px !important; margin: 0 0 10px 0; }}
        .hero p {{ color: white !important; font-size: 16px; margin: 0; }}
        .task-card {{
            background: {CARD}; border: 1px solid #E6E8EF; border-radius: 16px;
            padding: 16px 20px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
        }}
        .task-title {{ font-size: 20px; font-weight: 750; color: {TEXT}; margin: 3px 0 5px 0; }}
        .task-meta {{ font-size: 14px; color: {MUTED}; margin-bottom: 5px; }}
        .task-desc {{ font-size: 14px; color: #7A7F8C; margin: 8px 0 10px 0; }}
        .pill {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; margin-bottom: 6px; }}
        .critical {{ background: #FDE2E2; color: #A60000; }}
        .high {{ background: #FFE8CC; color: #A64B00; }}
        .normal {{ background: #FFF3BF; color: #7A5A00; }}
        .low {{ background: #DFF5E1; color: #1E6B2D; }}
        .workspace-button {{
            display: inline-block; background: {PRIMARY}; color: white !important; text-decoration: none;
            padding: 8px 13px; border-radius: 10px; font-size: 13px; font-weight: 750;
        }}
        .muted {{ color: {MUTED}; font-size: 14px; }}
        .empty {{ background: white; border: 1px dashed #D1D5DB; padding: 18px; border-radius: 14px; color: {MUTED}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>',
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
    if "Aktiv" not in df.columns:
        return df
    return df[df["Aktiv"].fillna("Ja").astype(str).str.strip().str.lower().isin(["ja", "yes", "1", "true"])]


def available_weeks(availability: pd.DataFrame) -> list[str]:
    return [c for c in availability.columns if str(c).startswith("U")]


def availability_for_person(availability: pd.DataFrame, person: str, week: str) -> str:
    if week not in availability.columns or "Navn" not in availability.columns:
        return "Arbejde"
    row = availability[availability["Navn"].astype(str).str.strip() == person]
    if row.empty:
        return "Arbejde"
    value = clean(row.iloc[0][week])
    return value if value else "Arbejde"


def workspace_link_map(workspaces: pd.DataFrame) -> dict[tuple[str, str], str]:
    mapping = {}
    for _, row in workspaces.iterrows():
        system = clean(row.get("System"))
        workspace = clean(row.get("Workspace"))
        link = clean(row.get("Link"))
        if system or workspace:
            mapping[(system, workspace)] = link
    return mapping


def enrich_tasks(tasks: pd.DataFrame, workspaces: pd.DataFrame) -> pd.DataFrame:
    tasks = tasks.copy()
    links = workspace_link_map(workspaces)
    tasks["__link"] = tasks.apply(lambda r: links.get((clean(r.get("System")), clean(r.get("Workspace"))), ""), axis=1)
    tasks["__prio"] = tasks["Prioritet"].map(PRIORITY_ORDER).fillna(99) if "Prioritet" in tasks.columns else 99
    return tasks.sort_values(["__prio", "Frekvens", "Arbejdsopgave"], na_position="last")


def tasks_for_person(tasks: pd.DataFrame, person: str) -> pd.DataFrame:
    cols = [c for c in ["Primær", "Backup", "Ferieafløser"] if c in tasks.columns]
    if not cols:
        return tasks.iloc[0:0]
    mask = False
    for col in cols:
        mask = mask | (tasks[col].astype(str).str.strip() == person)
    return tasks[mask]


def task_card(row: pd.Series) -> None:
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

    desc_html = f'<div class="task-desc">{esc(desc)}</div>' if desc else ""
    link_html = f'<a class="workspace-button" href="{esc(link)}" target="_blank">Open Workspace</a>' if link else '<div class="muted">No direct workspace link</div>'
    pill_html = f'<span class="pill {css_class}">{esc(label)}</span>' if label else ""

    st.markdown(
        f"""
        <div class="task-card">
            {pill_html}
            <div class="task-title">{esc(title)}</div>
            <div class="task-meta">{esc(meta)}</div>
            {desc_html}
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tasks(title: str, df: pd.DataFrame) -> None:
    st.markdown(f"## {esc(title)}")
    if df.empty:
        st.markdown('<div class="empty">No tasks found.</div>', unsafe_allow_html=True)
        return
    for _, row in df.iterrows():
        task_card(row)


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

    weeks = available_weeks(availability)
    people = team["Navn"].dropna().astype(str).tolist() if "Navn" in team.columns else []

    with st.sidebar:
        week = st.selectbox("Week", weeks, index=0 if weeks else None)
        person = st.selectbox("Person", people, index=0 if people else None)
        page = st.radio("Navigation", ["Start Day", "My Tasks", "Team", "Projects", "About"])

    if not person or not week:
        st.warning("Please select a week and a person.")
        return

    status = availability_for_person(availability, person, week)
    hero(f"Good morning {person} 👋", f"{week} · Availability: {status}")

    enriched = enrich_tasks(tasks, workspaces)
    person_tasks = tasks_for_person(enriched, person)

    if page == "Start Day":
        start = person_tasks[person_tasks.get("Start dagen", "").astype(str).str.strip().str.lower().eq("ja")]
        render_tasks("Start Day", start)
    elif page == "My Tasks":
        render_tasks("Daily", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Daglig")])
        render_tasks("Weekly", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Ugentlig")])
        render_tasks("Monthly", person_tasks[person_tasks.get("Frekvens", "").astype(str).str.strip().eq("Månedlig")])
    elif page == "Team":
        st.markdown("## Team")
        st.dataframe(team, use_container_width=True, hide_index=True)
    elif page == "Projects":
        st.markdown("## Projects")
        st.dataframe(projects, use_container_width=True, hide_index=True)
    elif page == "About":
        st.markdown("## About PE Planner")
        st.write("Version: WebApp recovery build")
        st.write(f"Employees: {len(team)}")
        st.write(f"Recurring tasks: {len(tasks)}")
        st.write(f"Projects / ad hoc rows: {len(projects)}")


if __name__ == "__main__":
    main()
