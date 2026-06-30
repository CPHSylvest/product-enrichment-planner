import streamlit as st
import pandas as pd
from components.ui import inject_css, hero, task_card
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
assignments = assignments.sort_values(["_prio", "Arbejdsopgave"])

my_assignments = assignments[assignments["Assigned to"].astype(str).eq(selected_person)]

if page == "Start Day":
    status = availability_for_person(availability, selected_person, selected_week)
    hero(f"Good morning {selected_person} 👋", f"{selected_week} · Availability: {status}")

    start_tasks = my_assignments[my_assignments["Start dagen"].fillna("").astype(str).str.lower().eq("ja")]
    st.header("Start Day")
    if start_tasks.empty:
        st.info("No Start Day tasks assigned.")
    for _, row in start_tasks.iterrows():
        task_card(row)

    st.header("Next Tasks")
    next_tasks = my_assignments[~my_assignments.index.isin(start_tasks.index)]
    if next_tasks.empty:
        st.success("No additional recurring tasks for this person.")
    for _, row in next_tasks.head(5).iterrows():
        task_card(row)

elif page == "My Tasks":
    hero("My Tasks", f"{selected_person} · {selected_week}")
    for freq in ["Daglig", "Ugentlig", "Månedlig"]:
        subset = my_assignments[my_assignments["Frekvens"].astype(str).eq(freq)]
        st.header(freq)
        if subset.empty:
            st.caption("No tasks")
        for _, row in subset.iterrows():
            task_card(row)

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
    st.write("Primary color: #000066")
    st.write("Excel is the administration tool. The web app is the work tool.")
