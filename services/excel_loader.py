import pandas as pd

SHEETS = {
    "team": "Team",
    "tasks": "Arbejdsopgaver",
    "workspaces": "Workspaces",
    "availability": "Tilgængelighed",
    "projects": "Plan & Projekter",
    "settings": "Settings",
}


def read_plan(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    data = {}
    for key, sheet in SHEETS.items():
        if sheet in xls.sheet_names:
            data[key] = pd.read_excel(uploaded_file, sheet_name=sheet)
        else:
            data[key] = pd.DataFrame()
    return data


def active_rows(df):
    if df.empty or "Aktiv" not in df.columns:
        return df
    return df[df["Aktiv"].astype(str).str.strip().str.lower().isin(["ja", "yes", "true", "1"])]


def workspace_map(workspaces):
    mapping = {}
    if workspaces.empty:
        return mapping
    for _, row in workspaces.iterrows():
        system = str(row.get("System", "")).strip()
        workspace = str(row.get("Workspace", "")).strip()
        link = row.get("Link", "")
        try:
            if pd.isna(link):
                link = ""
        except Exception:
            pass
        mapping[(system, workspace)] = str(link).strip()
    return mapping


def available_weeks(availability):
    if availability.empty:
        return []
    return [c for c in availability.columns if str(c).startswith("U")]


def availability_for(availability, person, week):
    if availability.empty or not person or not week:
        return "Arbejde"
    if "Navn" not in availability.columns or week not in availability.columns:
        return "Arbejde"
    rows = availability[availability["Navn"].astype(str).str.strip() == str(person).strip()]
    if rows.empty:
        return "Arbejde"
    value = rows.iloc[0][week]
    try:
        if pd.isna(value):
            return "Arbejde"
    except Exception:
        pass
    text = str(value).strip()
    return text if text else "Arbejde"
