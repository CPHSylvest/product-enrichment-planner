import pandas as pd

REQUIRED_SHEETS = [
    "Team",
    "Arbejdsopgaver",
    "Workspaces",
    "Tilgængelighed",
    "Plan & Projekter",
    "Settings",
]

UNAVAILABLE_VALUES = {"ferie", "fridag", "kursus", "syg"}


def load_plan(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    missing = [s for s in REQUIRED_SHEETS if s not in xls.sheet_names]
    if missing:
        raise ValueError("Missing sheets: " + ", ".join(missing))

    data = {sheet: pd.read_excel(uploaded_file, sheet_name=sheet) for sheet in REQUIRED_SHEETS}
    return data


def active_team(team_df):
    df = team_df.copy()
    if "Aktiv" in df.columns:
        df = df[df["Aktiv"].fillna("").astype(str).str.lower().eq("ja")]
    return df


def week_columns(availability_df):
    return [c for c in availability_df.columns if str(c).startswith("U")]


def availability_for_person(availability_df, person, week):
    if availability_df.empty or week not in availability_df.columns:
        return "Arbejde"
    row = availability_df[availability_df["Navn"].astype(str).eq(str(person))]
    if row.empty:
        return "Arbejde"
    value = row.iloc[0][week]
    if pd.isna(value) or str(value).strip() == "":
        return "Arbejde"
    return str(value).strip()


def is_available(availability_df, person, week):
    return availability_for_person(availability_df, person, week).lower() not in UNAVAILABLE_VALUES


def assigned_person(row, availability_df, week):
    primary = row.get("Primær", "")
    backup = row.get("Backup", "")
    vacation_backup = row.get("Ferieafløser", "")

    if primary and is_available(availability_df, primary, week):
        return primary, "Primary", ""
    if backup and is_available(availability_df, backup, week):
        return backup, "Backup", primary
    if vacation_backup and is_available(availability_df, vacation_backup, week):
        return vacation_backup, "Vacation backup", primary
    return "REQUIRES STAFFING", "Unassigned", primary


def build_assignments(tasks_df, availability_df, week):
    df = tasks_df.copy()
    if "Aktiv" in df.columns:
        df = df[df["Aktiv"].fillna("").astype(str).str.lower().eq("ja")]

    assigned = df.apply(lambda r: assigned_person(r, availability_df, week), axis=1)
    df["Assigned to"] = [x[0] for x in assigned]
    df["Assignment type"] = [x[1] for x in assigned]
    df["Taken over from"] = [x[2] for x in assigned]
    return df


def enrich_with_workspace(tasks_df, workspaces_df):
    df = tasks_df.copy()
    ws = workspaces_df.copy()
    if ws.empty:
        df["Link"] = ""
        df["Åbn i nyt vindue"] = "Ja"
        return df
    keep = [c for c in ["System", "Workspace", "Link", "Åbn i nyt vindue"] if c in ws.columns]
    ws = ws[keep].drop_duplicates(subset=["System", "Workspace"], keep="first")
    return df.merge(ws, on=["System", "Workspace"], how="left")


def priority_sort_value(value):
    order = {"Kritisk": 1, "Høj": 2, "Normal": 3, "Lav": 4}
    return order.get(str(value).strip(), 99)
