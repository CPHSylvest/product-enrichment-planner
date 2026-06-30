import streamlit as st

st.set_page_config(
    page_title="Product Enrichment Planner",
    page_icon="📋",
    layout="wide"
)

st.title("Product Enrichment Planner")
st.write("Appen virker ✅")

uploaded_file = st.file_uploader("Upload Excel-fil", type=["xlsx"])

if uploaded_file:
    st.success("Excel-filen er uploadet.")
else:
    st.info("Upload en Excel-fil for at starte.")
