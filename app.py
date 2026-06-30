import streamlit as st
import pandas as pd
from components.ui import inject_css, hero, task_card, section, clean
from services.excel_service import (
    load_plan,
    active_team,
    week_columns,
    build_assignments,
    enrich_with_workspace,
    priority_sort_value,
    availability_for_person,
)

st.set_page_config(page_title="PE Planner", page_icon="📋", layout="wide")
inject_css()

st.sidebar.title("PE Planner")
uploaded = st.sidebar.file_uploader("Import Plan", type=["xlsx"])

if uploaded is None:
    hero("PE Planner", "Import PE Planner Administration to start.")
    st.info("Use the sidebar to import your PE Planner Administration Excel file.")
    st.stop()

try:
    data = load_plan(uploaded)
except Exception as e:
    hero("Import error", "The uploaded file could not be read.")
    st.error(str(e))
    st.stop()

team = active_team(data["Team"])
tasks = data["Arbejdsopgaver"]
workspaces = data["Workspaces"]
availability = data["Tilgængelighed"]
projects = data["Plan & Projekter"]

weeks = week_columns(availability)
selected_week = st.sidebar.selectbox("Week", weeks if weeks else ["U1"])
people = team["Navn"].dropna().astype(str).tolist()
selected_person = st.sidebar.selectbox("Person", people)
page = st.sidebar.radio("Navigation", ["Start Day", "My Tasks", "Team", "Projects", "About"])

assignments = build_assignments(tasks, availability, selected_week)
assignments = enrich_with_workspace(assignments, workspaces)
assignments["_prio"] = assignments["Prioritet"].apply(priority_sort_value)
assignments = assignments.sort_values(["_prio", "Frekvens", "Arbejdsopgave"])
my_assignments = assignments[assignments["Assigned to"].astype(str).eq(selected_person)]


def show_group(title, df):
    section(f"{title} ({len(df)})")
    if df.empty:
        st.caption("No tasks")
        return
    for _, row in df.iterrows():
        task_card(row)


if page == "Start Day":
    status = availability_for_person(availability, selected_person, selected_week)
    hero(f"Good morning {selected_person} 👋", f"{selected_week} · Availability: {status}")

    start_tasks = my_assignments[my_assignments["Start dagen"].fillna("").astype(str).str.lower().eq("ja")]
    show_group("Start Day", start_tasks)

    critical_next = my_assignments[
        (~my_assignments.index.isin(start_tasks.index))
        & (my_assignments["Prioritet"].astype(str).str.lower().str.contains("kritisk|critical", na=False))
    ]
    high_next = my_assignments[
        (~my_assignments.index.isin(start_tasks.index))
        & (my_assignments["Prioritet"].astype(str).str.lower().str.contains("høj|hoej|high", na=False))
        & (~my_assignments.index.isin(critical_next.index))
    ]
    other_next = my_assignments[
        (~my_assignments.index.isin(start_tasks.index))
        & (~my_assignments.index.isin(critical_next.index))
        & (~my_assignments.index.isin(high_next.index))
    ]
    if not critical_next.empty:
        show_group("Critical next", critical_next)
    if not high_next.empty:
        show_group("High priority next", high_next)
    if not other_next.empty:
        show_group("Other tasks", other_next.head(6))

elif page == "My Tasks":
    hero("My Tasks", f"{selected_person} · {selected_week}")
    daily = my_assignments[my_assignments["Frekvens"].astype(str).eq("Daglig")]
    weekly = my_assignments[my_assignments["Frekvens"].astype(str).eq("Ugentlig")]
    monthly = my_assignments[my_assignments["Frekvens"].astype(str).eq("Månedlig")]
    show_group("Daily", daily)
    show_group("Weekly", weekly)
    show_group("Monthly", monthly)

elif page == "Team":
    hero("Team", "Active Product Enrichment team")
    st.dataframe(team, use_container_width=True, hide_index=True)

elif page == "Projects":
    hero("Projects", "Ad hoc planning and project tasks")
    if "Ansvarlig" in projects.columns:
        my_projects = projects[projects["Ansvarlig"].astype(str).eq(selected_person)]
    else:
        my_projects = projects
    st.dataframe(my_projects, use_container_width=True, hide_index=True)

elif page == "About":
    hero("About PE Planner", "Product Enrichment Planning & Capacity Management")
    col1, col2, col3 = st.columns(3)
    col1.metric("Active people", len(team))
    col2.metric("Recurring tasks", len(tasks))
    col3.metric("Project rows", len(projects))
    st.write("Primary color: #000066 / interface navy adjusted darker.")
    st.write("Excel is the administration tool. The web app is the work tool.")
