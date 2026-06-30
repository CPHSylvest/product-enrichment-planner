import pandas as pd
import streamlit as st

NAVY = "#000033"
PRIMARY = "#000066"
BG = "#F5F6FA"
TEXT = "#2B2D3A"
MUTED = "#697386"

PRIORITY_ORDER = {"Kritisk": 1, "Høj": 2, "Normal": 3, "Lav": 4}
PRIORITY_LABELS = {"Kritisk": "Critical", "Høj": "High", "Normal": "Normal", "Lav": "Low"}


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
    st.markdown(f"""
    <style>
    .stApp {{ background: {BG}; }}
    section[data-testid="stSidebar"] {{ background: {NAVY}; }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea {{
        color: {TEXT} !important;
        background: white !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {{
        color: {TEXT} !important;
    }}
    h1 {{ font-size: 2.0rem !important; color: {TEXT}; }}
    h2 {{ font-size: 1.45rem !important; color: {TEXT}; margin-top: 1.0rem !important; }}
    h3 {{ font-size: 1.1rem !important; color: {TEXT}; }}
    .hero {{
        background: {NAVY}; color: white; border-radius: 22px;
        padding: 28px 34px; margin-bottom: 22px;
    }}
    .hero h1 {{ color: white !important; font-size: 2.2rem !important; margin-bottom: 8px; }}
    .hero p {{ color: white; font-size: 1rem; margin: 0; }}
    .task-card {{
        background: white; border: 1px solid #E2E6EF; border-radius: 16px;
        padding: 16px 18px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }}
    .task-title {{ font-size: 1.15rem; font-weight: 700; color: {TEXT}; margin-bottom: 4px; }}
    .task-meta {{ color: {MUTED}; font-size: .88rem; margin-bottom: 4px; }}
    .task-desc {{ color: {MUTED}; font-size: .88rem; margin-top: 4px; }}
    .pill {{ display: inline-block; border-radius: 999px; padding: 3px 10px; font-size: .75rem; font-weight: 700; margin-bottom: 6px; }}
    .critical {{ background: #FFE2E2; color: #A40000; }}
    .high {{ background: #FFECD6; color: #A85A00; }}
    .normal {{ background: #E8F0FF; color: #003A8C; }}
    .low {{ background: #E8F7ED; color: #1F7A3A; }}
    .open-link a {{
        display:inline-block; background:{PRIMARY}; color:white !important; text-decoration:none;
        padding:8px 13px; border-radius:10px; font-weight:700; margin-top:8px; font-size:.85rem;
    }}
    .section-label {{
        color:{TEXT}; font-size:1.0rem; font-weight:800; margin-top:18px; margin-bottom:4px;
        border-bottom:1px solid #D8DEE9; padding-bottom:6px;
    }}
    .small-note {{ color: {MUTED}; font-size: .9rem; }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f"""
    <div class="hero">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def priority_class(priority):
    p = clean(priority)
    return {"Kritisk": "critical", "Høj": "high", "Normal": "normal", "Lav": "low"}.get(p, "normal")


def task_card(row, workspace_link=""):
    title = clean(row.get("Arbejdsopgave"), "Untitled task")
    priority = clean(row.get("Prioritet"), "Normal")
    priority_en = PRIORITY_LABELS.get(priority, priority)
    system = clean(row.get("System"))
    workspace = clean(row.get("Workspace"))
    banner = clean(row.get("Banner"))
    frequency = clean(row.get("Frekvens"))
    minutes = clean(row.get("Estimeret tid")) or clean(row.get("Estimeret tid (min)")) or clean(row.get("Estimeret tid (min.)"))
    desc = clean(row.get("Beskrivelse"))
    meta_parts = []
    if system or workspace:
        meta_parts.append(" / ".join([x for x in [system, workspace] if x]))
    if banner:
        meta_parts.append(banner)
    if frequency:
        meta_parts.append(frequency)
    if minutes:
        meta_parts.append(f"{minutes} min")
    meta = " · ".join(meta_parts)
    link_html = ""
    if workspace_link:
        link_html = f'<div class="open-link"><a href="{workspace_link}" target="_blank">Open Workspace</a></div>'
    elif system or workspace:
        link_html = '<div class="small-note">No direct workspace link</div>'
    st.markdown(f"""
    <div class="task-card">
      <div class="pill {priority_class(priority)}">{priority_en}</div>
      <div class="task-title">{title}</div>
      <div class="task-meta">{meta}</div>
      <div class="task-desc">{desc}</div>
      {link_html}
    </div>
    """, unsafe_allow_html=True)
