import pandas as pd
import streamlit as st

NAVY = "#000033"
PRIMARY = "#000066"
BG = "#F5F6FA"

PRIORITY_ORDER = {
    "Kritisk": 1,
    "Høj": 2,
    "Normal": 3,
    "Lav": 4,
    "Critical": 1,
    "High": 2,
    "Low": 4,
}

def clean(value, default=""):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in ["nan", "none", "nat"]:
        return default
    return text

def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {BG};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {PRIMARY};
        }}

        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}

        h1 {{
            font-size: 38px !important;
            line-height: 1.1 !important;
        }}

        h2 {{
            font-size: 28px !important;
        }}

        h3 {{
            font-size: 22px !important;
        }}

        .hero {{
            background: {PRIMARY};
            color: white;
            padding: 34px 38px;
            border-radius: 26px;
            margin-bottom: 28px;
        }}

        .hero h1 {{
            color: white !important;
            margin-bottom: 12px;
        }}

        .hero p {{
            color: white !important;
            font-size: 17px;
        }}

        .task-card {{
            background: white;
            border-radius: 18px;
            padding: 20px 24px;
            margin-bottom: 14px;
            border: 1px solid #E6E8EF;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}

        .task-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #2B2E3A;
        }}

        .task-meta {{
            color: #666B78;
            font-size: 15px;
            margin-bottom: 6px;
        }}

        .task-desc {{
            color: #7A7F8C;
            font-size: 15px;
            margin-bottom: 12px;
        }}

        .priority-pill {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .priority-critical {{
            background: #FDE2E2;
            color: #A60000;
        }}

        .priority-high {{
            background: #FFE8CC;
            color: #A64B00;
        }}

        .priority-normal {{
            background: #FFF3BF;
            color: #7A5A00;
        }}

        .priority-low {{
            background: #DFF5E1;
            color: #1E6B2D;
        }}

        .workspace-link {{
            display: inline-block;
            background: {PRIMARY};
            color: white !important;
            padding: 9px 16px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 700;
            font-size: 14px;
        }}

        .stSelectbox label, .stFileUploader label {{
            color: white !important;
        }}

        div[data-baseweb="select"] * {{
            color: #1F2430 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hero(title, subtitle=""):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{clean(title)}</h1>
            <p>{clean(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def task_card(title, meta="", description="", priority="", link=""):
    priority_clean = clean(priority)
    priority_class = {
        "Kritisk": "priority-critical",
        "Critical": "priority-critical",
        "Høj": "priority-high",
        "High": "priority-high",
        "Normal": "priority-normal",
        "Lav": "priority-low",
        "Low": "priority-low",
    }.get(priority_clean, "priority-normal")

    priority_html = ""
    if priority_clean:
        priority_html = f'<div class="priority-pill {priority_class}">{priority_clean}</div>'

    desc_html = ""
    if clean(description):
        desc_html = f'<div class="task-desc">{clean(description)}</div>'

    link_html = ""
    if clean(link):
        link_html = f'<a class="workspace-link" href="{clean(link)}" target="_blank">Open Workspace</a>'

    st.markdown(
        f"""
        <div class="task-card">
            {priority_html}
            <div class="task-title">{clean(title)}</div>
            <div class="task-meta">{clean(meta)}</div>
            {desc_html}
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def section(title):
    st.markdown(f"## {clean(title)}")
