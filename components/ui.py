import streamlit as st

NAVY = "#000066"
WHITE = "#FFFFFF"


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: #F7F8FB; }}
        [data-testid="stSidebar"] {{ background: {NAVY}; }}
        [data-testid="stSidebar"] * {{ color: white !important; }}
        .hero {{
            background: {NAVY};
            color: white;
            padding: 28px 32px;
            border-radius: 22px;
            margin-bottom: 22px;
        }}
        .hero h1 {{ color: white; margin-bottom: 4px; }}
        .card {{
            background: white;
            border-radius: 18px;
            padding: 20px 22px;
            border: 1px solid #E6E8EF;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
            margin-bottom: 16px;
        }}
        .priority {{
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 999px;
            display: inline-block;
            margin-bottom: 8px;
        }}
        .kritisk {{ background:#FFE5E5; color:#990000; }}
        .hoej {{ background:#FFF0D9; color:#8A4B00; }}
        .normal {{ background:#FFF9CC; color:#6B5A00; }}
        .lav {{ background:#EAF7EA; color:#236B23; }}
        .meta {{ color:#5F6673; font-size: 14px; }}
        .takeover {{ color:#8A4B00; font-weight: 700; }}
        div.stButton > button, div.stDownloadButton > button {{
            background-color: {NAVY};
            color: white;
            border-radius: 12px;
            border: 0;
            padding: 0.65rem 1rem;
            font-weight: 700;
        }}
        a[data-testid="stLinkButton"] {{
            background-color: {NAVY};
            color: white !important;
            border-radius: 12px;
            border: 0;
            padding: 0.55rem 1rem;
            font-weight: 700;
            text-decoration: none;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle=""):
    st.markdown(f'<div class="hero"><h1>{title}</h1><div>{subtitle}</div></div>', unsafe_allow_html=True)


def priority_class(priority):
    value = str(priority).lower()
    if "kritisk" in value:
        return "kritisk"
    if "høj" in value or "hoej" in value:
        return "hoej"
    if "lav" in value:
        return "lav"
    return "normal"


def task_card(row):
    prio = row.get("Prioritet", "Normal")
    title = row.get("Arbejdsopgave", "Task")
    system = row.get("System", "")
    workspace = row.get("Workspace", "")
    banner = row.get("Banner", "")
    freq = row.get("Frekvens", "")
    minutes = row.get("Estimeret tid", row.get("Estimeret tid (min)", ""))
    assignment_type = row.get("Assignment type", "")
    takeover = row.get("Taken over from", "")
    desc = row.get("Beskrivelse", "")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<span class="priority {priority_class(prio)}">{prio}</span>', unsafe_allow_html=True)
    st.subheader(str(title))
    st.markdown(f'<div class="meta">{system} / {workspace} · {banner} · {freq} · {minutes} min</div>', unsafe_allow_html=True)
    if assignment_type in ["Backup", "Vacation backup"] and takeover:
        st.markdown(f'<div class="takeover">Taken over from {takeover}</div>', unsafe_allow_html=True)
    if desc and str(desc) != "nan":
        st.caption(str(desc))
    link = row.get("Link", "")
    if link and str(link) != "nan":
        st.link_button("Open Workspace", str(link))
    else:
        st.caption("No direct workspace link")
    st.markdown('</div>', unsafe_allow_html=True)
