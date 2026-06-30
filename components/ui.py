import pandas as pd
import streamlit as st

NAVY = "#000033"
PRIMARY = "#000066"
BG = "#F5F6FA"
BORDER = "#E2E6F0"
TEXT = "#111827"
MUTED = "#667085"


def clean(value, default=""):
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


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {BG}; color: {TEXT}; }}
        [data-testid="stSidebar"] {{ background: {NAVY}; }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{ color: white !important; }}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {TEXT} !important; }}
        [data-testid="stSidebar"] [data-baseweb="radio"] * {{ color: white !important; }}
        .block-container {{ padding-top: 1.3rem; padding-bottom: 2rem; max-width: 1180px; }}
        h1 {{ font-size: 1.55rem !important; margin-bottom: .2rem !important; }}
        h2 {{ font-size: 1.15rem !important; margin-top: .8rem !important; margin-bottom: .45rem !important; }}
        h3 {{ font-size: 1rem !important; }}
        .hero {{
            background: {NAVY}; color: white; padding: 16px 20px;
            border-radius: 16px; margin-bottom: 14px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.10);
        }}
        .hero h1 {{ color: white !important; font-size: 1.45rem !important; margin: 0 0 2px 0 !important; }}
        .hero .subtitle {{ color: #E9ECF7; font-size: .9rem; }}
        .section-title {{
            font-weight: 800; font-size: .88rem; color: {NAVY};
            text-transform: uppercase; letter-spacing: .04em; margin: 12px 0 6px 0;
            border-bottom: 1px solid {BORDER}; padding-bottom: 4px;
        }}
        .task-card {{
            background: white; border: 1px solid {BORDER}; border-radius: 12px;
            padding: 10px 12px; margin-bottom: 8px;
            box-shadow: 0 1px 4px rgba(16,24,40,0.04);
        }}
        .task-top {{ display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }}
        .task-title {{ font-size: 1.0rem; font-weight: 800; color: {TEXT}; line-height:1.2; }}
        .task-meta {{ color:{MUTED}; font-size:.82rem; margin-top:3px; }}
        .task-desc {{ color:#475467; font-size:.8rem; margin-top:5px; }}
        .badge {{
            font-size: .70rem; font-weight: 800; padding: 3px 8px; border-radius: 999px;
            white-space: nowrap; display:inline-block;
        }}
        .kritisk {{ background:#FEE4E2; color:#B42318; }}
        .hoej {{ background:#FEF0C7; color:#B54708; }}
        .normal {{ background:#E0F2FE; color:#026AA2; }}
        .lav {{ background:#ECFDF3; color:#027A48; }}
        .takeover {{ color:#B54708; font-weight:700; font-size:.8rem; margin-top:4px; }}
        div.stButton > button, div.stDownloadButton > button {{
            background-color: {PRIMARY}; color: white; border-radius: 10px; border: 0;
            padding: 0.45rem .75rem; font-weight: 700; font-size:.85rem;
        }}
        a[data-testid="stLinkButton"] {{
            background-color: {PRIMARY}; color: white !important; border-radius: 10px; border: 0;
            padding: 0.35rem .65rem; font-weight: 700; text-decoration: none; font-size:.82rem;
        }}
        .stSelectbox div[data-baseweb="select"] > div {{ background:white; color:{TEXT}; }}
        .stSelectbox div[data-baseweb="select"] span {{ color:{TEXT} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle=""):
    st.markdown(
        f'<div class="hero"><h1>{clean(title)}</h1><div class="subtitle">{clean(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="section-title">{clean(title)}</div>', unsafe_allow_html=True)


def priority_class(priority):
    value = clean(priority).lower()
    if "kritisk" in value or "critical" in value:
        return "kritisk"
    if "høj" in value or "hoej" in value or "high" in value:
        return "hoej"
    if "lav" in value or "low" in value:
        return "lav"
    return "normal"


def task_card(row, compact=False):
    prio = clean(row.get("Prioritet"), "Normal")
    title = clean(row.get("Arbejdsopgave"), "Task")
    system = clean(row.get("System"))
    workspace = clean(row.get("Workspace"))
    banner = clean(row.get("Banner"))
    freq = clean(row.get("Frekvens"))
    minutes = clean(row.get("Estimeret tid"), clean(row.get("Estimeret tid (min)")))
    assignment_type = clean(row.get("Assignment type"))
    takeover = clean(row.get("Taken over from"))
    desc = clean(row.get("Beskrivelse"))
    link = clean(row.get("Link"))

    meta_parts = []
    if system or workspace:
        meta_parts.append(" / ".join([p for p in [system, workspace] if p]))
    for item in [banner, freq, f"{minutes} min" if minutes else ""]:
        if item:
            meta_parts.append(item)
    meta = " · ".join(meta_parts)

    st.markdown('<div class="task-card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="task-top"><div><div class="task-title">{title}</div><div class="task-meta">{meta}</div></div>'
        f'<span class="badge {priority_class(prio)}">{prio}</span></div>',
        unsafe_allow_html=True,
    )
    if assignment_type in ["Backup", "Vacation backup"] and takeover:
        st.markdown(f'<div class="takeover">Taken over from {takeover}</div>', unsafe_allow_html=True)
    if desc:
        st.markdown(f'<div class="task-desc">{desc}</div>', unsafe_allow_html=True)
    if link:
        st.link_button("Open Workspace", link)
    elif system or workspace:
        st.caption("Workspace has no direct link")
    st.markdown('</div>', unsafe_allow_html=True)
