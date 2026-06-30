import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PE Planner",
    page_icon="📋",
    layout="wide"
)

REQUIRED_SHEETS = [
    "Team",
    "Arbejdsopgaver",
    "Calendar",
    "Extra Tasks",
    "Monthly Tasks"
]

st.title("📋 PE Planner")
st.caption("Product Enrichment Planning & Capacity Management")

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Vælg side",
    [
        "Dashboard",
        "Mine opgaver",
        "Team",
        "Plan",
        "Arbejdsopgaver",
        "Ekstra opgaver",
        "Administration"
    ]
)

uploaded_file = st.sidebar.file_uploader(
    "Importer plan",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload PE Planner Excel-filen i venstremenuen for at starte.")
    st.stop()

try:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    missing_sheets = [
        sheet for sheet in REQUIRED_SHEETS
        if sheet not in sheet_names
    ]

    if missing_sheets:
        st.error("Excel-filen mangler følgende ark:")
        st.write(missing_sheets)
        st.stop()

    team = pd.read_excel(uploaded_file, sheet_name="Team")
    tasks = pd.read_excel(uploaded_file, sheet_name="Arbejdsopgaver")
    calendar = pd.read_excel(uploaded_file, sheet_name="Calendar")
    extra_tasks = pd.read_excel(uploaded_file, sheet_name="Extra Tasks")
    monthly_tasks = pd.read_excel(uploaded_file, sheet_name="Monthly Tasks")

except Exception as e:
    st.error("Excel-filen kunne ikke læses.")
    st.exception(e)
    st.stop()

if page == "Dashboard":
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Medarbejdere", len(team))
    col2.metric("Arbejdsopgaver", len(tasks))
    col3.metric("Ekstra opgaver", len(extra_tasks))
    col4.metric("Månedlige opgaver", len(monthly_tasks))

    st.subheader("Arbejdsopgaver")
    st.dataframe(tasks, use_container_width=True)

elif page == "Mine opgaver":
    st.header("Mine opgaver")

    people = team["Navn"].dropna().unique().tolist()

    selected_person = st.selectbox("Vælg person", people)

    my_tasks = tasks[
        (tasks["Primær"] == selected_person) |
        (tasks["Backup"] == selected_person) |
        (tasks["Ferieafløser"] == selected_person)
    ]

    st.subheader(selected_person)
    st.dataframe(my_tasks, use_container_width=True)

elif page == "Team":
    st.header("Team")
    st.dataframe(team, use_container_width=True)

elif page == "Plan":
    st.header("Plan / ferie / fridage")
    st.dataframe(calendar, use_container_width=True)

elif page == "Arbejdsopgaver":
    st.header("Arbejdsopgaver")
    st.dataframe(tasks, use_container_width=True)

elif page == "Ekstra opgaver":
    st.header("Ekstra opgaver")
    st.dataframe(extra_tasks, use_container_width=True)

elif page == "Administration":
    st.header("Administration")

    st.success("Excel-filen er indlæst korrekt.")

    st.write("Fundne ark:")
    st.write(sheet_names)

    st.write("Forventede ark:")
    st.write(REQUIRED_SHEETS)
