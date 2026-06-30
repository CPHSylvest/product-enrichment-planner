import pandas as pd
import streamlit as st
from components.ui import inject_css, hero, task_card, clean, PRIORITY_ORDER
from services.excel_loader import read_plan, active_rows, workspace_map, available_weeks, availability_for

st.set_page_config(page_title="PE Planner", page_icon="📋", layout="wide")
inject_css()

with st.sidebar:
    st.markdown("# PE Planner")
    uploaded = st.file_uploader("Import Plan", type=["xlsx"])

if not uploaded:
    hero("PE Planner", "Import PE Planner Administration to start.")
    st.info("Use the sidebar to import your PE Planner Administration Excel file.")
    st.stop()

data = read_plan(uploaded)
team = active_rows(data["team"])
tasks = active_rows(data["tasks"])
workspaces = active_rows(data["workspaces"])
availability = data["availability"]
projects = data["projects"]
links = workspace_map(workspaces)
weeks = available_weeks(availability)

with st.sidebar:
    week = st.selectbox("Week", weeks if weeks else [""], index=0)
    people = team["Navn"].dropna().astype(str).tolist() if "Navn" in team.columns else []
    person = st.selectbox("Person", people if people else [""], index=0)
    page = st.radio("Navigation", ["Start Day", "My Tasks", "Team", "Projects", "About"])

availability_status = availability_for(availability, person, week)

if page == "Start Day":
    hero(f"Good morning {person} 👋", f"{week} · Availability: {availability_status}")
    st.markdown("## Start Day")
    if tasks.empty:
        st.warning("No tasks found.")
    else:
        df = tasks.copy()
        if "Primær" in df.columns:
            df = df[df["Primær"].astype(str).str.strip() == str(person).strip()]
        if "Start dagen" in df.columns:
            df = df[df["Start dagen"].astype(str).str.strip().str.lower() == "ja"]
        df["_prio"] = df.get("Prioritet", "Normal").map(PRIORITY_ORDER).fillna(99)
        df = df.sort_values(["_prio", "Arbejdsopgave"])
        if df.empty:
            st.info("No Start Day tasks for this person.")
        for _, row in df.iterrows():
            link = links.get((clean(row.get("System")), clean(row.get("Workspace"))), "")
            task_card(row, link)

elif page == "My Tasks":
    hero("My Tasks", f"{person} · {week}")
    df = tasks.copy()
    if "Primær" in df.columns:
        df = df[df["Primær"].astype(str).str.strip() == str(person).strip()]
    if df.empty:
        st.info("No tasks found for this person.")
    else:
        if "Prioritet" in df.columns:
            df["_prio"] = df["Prioritet"].map(PRIORITY_ORDER).fillna(99)
            df = df.sort_values(["_prio", "Frekvens", "Arbejdsopgave"])
        for freq in ["Daglig", "Ugentlig", "Månedlig"]:
            sub = df[df.get("Frekvens", "").astype(str).str.strip() == freq]
            if not sub.empty:
                st.markdown(f'<div class="section-label">{freq}</div>', unsafe_allow_html=True)
                for _, row in sub.iterrows():
                    link = links.get((clean(row.get("System")), clean(row.get("Workspace"))), "")
                    task_card(row, link)

elif page == "Team":
    hero("Team", "Active employees")
    st.dataframe(team, use_container_width=True, hide_index=True)

elif page == "Projects":
    hero("Projects", "Plan & Projects")
    if projects.empty:
        st.info("No projects found.")
    else:
        st.dataframe(projects, use_container_width=True, hide_index=True)

elif page == "About":
    hero("About PE Planner", "Product Enrichment Planning & Capacity Management")
    c1, c2, c3 = st.columns(3)
    c1.metric("Employees", len(team))
    c2.metric("Tasks", len(tasks))
    c3.metric("Projects", 0 if projects.empty else len(projects))
    st.write("Version: WebApp v0.2 fixed")
