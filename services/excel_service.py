import pandas as pd

UNAVAILABLE_STATUSES = {"Ferie", "Fridag", "Kursus", "Syg"}
ACTIVE_VALUES = {"ja", "yes", "true", "1"}
PRIORITY_ORDER = {"Kritisk": 1, "Høj": 2, "Normal": 3, "Lav": 4}
FREQUENCY_ORDER = {"Daglig": 1, "Ugentlig": 2, "Månedlig": 3}


def clean(value, default=""):
    """Return a safe string. Prevents NaN/None from being shown in the app."""
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


def is_active_row(row):
    """Rows are active unless an Aktiv column explicitly says otherwise."""
    if "Aktiv" not in row.index:
        return True
    value = clean(row.get("Aktiv")).lower()
    if value == "":
        return True
    return value in ACTIVE_VALUES


def active_rows(df):
    """Return only active rows from a dataframe."""
    if df is None or df.empty:
        return pd.DataFrame()
    if "Aktiv" not in df.columns:
        return df.copy()
    return df[df.apply(is_active_row, axis=1)].copy()


def get_available_weeks(availability_df):
    """Return all week columns, e.g. U1, U2, ..., U52."""
    if availability_df is None or availability_df.empty:
        return []
    return [col for col in availability_df.columns if str(col).strip().startswith("U")]


def availability_status(availability_df, person, week):
    """
    Return the status for a person in a selected week.
    Blank cell means Arbejde.
    """
    person = clean(person)
    week = clean(week)

    if not person or not week:
        return "Arbejde"
    if availability_df is None or availability_df.empty:
        return "Arbejde"
    if "Navn" not in availability_df.columns or week not in availability_df.columns:
        return "Arbejde"

    rows = availability_df[
        availability_df["Navn"].apply(lambda x: clean(x).lower()) == person.lower()
    ]

    if rows.empty:
        return "Arbejde"

    value = clean(rows.iloc[0][week])
    return value if value else "Arbejde"


def is_available(availability_df, person, week):
    """Return True if person is available in selected week."""
    status = availability_status(availability_df, person, week)
    return status not in UNAVAILABLE_STATUSES


def workspace_links(workspaces_df):
    """Create lookup from (System, Workspace) to link/icon."""
    links = {}
    if workspaces_df is None or workspaces_df.empty:
        return links

    df = active_rows(workspaces_df)
    for _, row in df.iterrows():
        system = clean(row.get("System"))
        workspace = clean(row.get("Workspace"))
        if not system and not workspace:
            continue
        links[(system, workspace)] = {
            "link": clean(row.get("Link")),
            "icon": clean(row.get("Ikon")),
            "open_new_window": clean(row.get("Åbn i nyt vindue"), "Ja"),
        }
    return links


def _assign_single_task(task_row, availability_df, week):
    """
    Assign one task to exactly one person if possible.
    Order: Primær -> Backup -> Ferieafløser -> Requires Staffing.
    """
    result = task_row.to_dict()

    primary = clean(task_row.get("Primær"))
    backup = clean(task_row.get("Backup"))
    substitute = clean(task_row.get("Ferieafløser"))

    result["Assigned To"] = ""
    result["Taken Over From"] = ""
    result["Assignment Role"] = ""
    result["Requires Staffing"] = False
    result["Staffing Reason"] = ""

    if primary and is_available(availability_df, primary, week):
        result["Assigned To"] = primary
        result["Assignment Role"] = "Primary"
        return result

    if backup and is_available(availability_df, backup, week):
        result["Assigned To"] = backup
        result["Taken Over From"] = primary
        result["Assignment Role"] = "Backup"
        return result

    if substitute and is_available(availability_df, substitute, week):
        result["Assigned To"] = substitute
        result["Taken Over From"] = primary
        result["Assignment Role"] = "Vacation Cover"
        return result

    unavailable = []
    for label, person in [
        ("Primary", primary),
        ("Backup", backup),
        ("Vacation Cover", substitute),
    ]:
        if person:
            unavailable.append(f"{label}: {person} ({availability_status(availability_df, person, week)})")
        else:
            unavailable.append(f"{label}: missing")

    result["Requires Staffing"] = True
    result["Staffing Reason"] = " | ".join(unavailable)
    return result


def build_assignments(tasks_df, availability_df, week):
    """
    Build assigned task list for selected week.

    Golden rules:
    - One task appears only once per week.
    - Primary -> Backup -> Ferieafløser.
    - Blank availability cell means Arbejde.
    - Ferie/Fridag/Kursus/Syg means unavailable.
    - If nobody is available, task becomes Requires Staffing.
    """
    if tasks_df is None or tasks_df.empty:
        return pd.DataFrame()

    tasks = active_rows(tasks_df)
    assigned = []

    for _, task_row in tasks.iterrows():
        assigned.append(_assign_single_task(task_row, availability_df, week))

    result = pd.DataFrame(assigned)
    return sort_tasks(result)


def sort_tasks(df):
    """Sort tasks by priority, frequency and task name."""
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()
    result["_priority_sort"] = result.get("Prioritet", "").apply(
        lambda x: PRIORITY_ORDER.get(clean(x), 99)
    )
    result["_frequency_sort"] = result.get("Frekvens", "").apply(
        lambda x: FREQUENCY_ORDER.get(clean(x), 99)
    )
    result["_task_sort"] = result.get("Arbejdsopgave", "").apply(clean)

    result = result.sort_values(["_priority_sort", "_frequency_sort", "_task_sort"])
    return result.drop(columns=["_priority_sort", "_frequency_sort", "_task_sort"], errors="ignore")


def tasks_for_person(assignments_df, person, include_requires_staffing=True):
    """
    Return tasks assigned to selected person.
    Requires Staffing tasks can be included for everyone.
    """
    if assignments_df is None or assignments_df.empty:
        return pd.DataFrame()

    person = clean(person)
    assigned = assignments_df[
        assignments_df["Assigned To"].apply(lambda x: clean(x).lower()) == person.lower()
    ]

    if include_requires_staffing:
        staffing = requires_staffing(assignments_df)
        combined = pd.concat([staffing, assigned], ignore_index=True)
        return sort_tasks(combined)

    return sort_tasks(assigned)


def start_day_tasks(assignments_df, person, include_requires_staffing=True):
    """Return Start Day tasks for selected person."""
    df = tasks_for_person(assignments_df, person, include_requires_staffing)
    if df.empty or "Start dagen" not in df.columns:
        return df

    start_day = df[
        (df["Requires Staffing"] == True)
        | (df["Start dagen"].apply(lambda x: clean(x).lower()) == "ja")
    ]
    return sort_tasks(start_day)


def requires_staffing(assignments_df):
    """Return all tasks requiring staffing."""
    if assignments_df is None or assignments_df.empty:
        return pd.DataFrame()
    if "Requires Staffing" not in assignments_df.columns:
        return pd.DataFrame()
    return assignments_df[assignments_df["Requires Staffing"] == True].copy()


def takeover_tasks(assignments_df):
    """Return all tasks taken over from a primary owner."""
    if assignments_df is None or assignments_df.empty:
        return pd.DataFrame()
    if "Taken Over From" not in assignments_df.columns:
        return pd.DataFrame()
    return assignments_df[assignments_df["Taken Over From"].apply(lambda x: clean(x) != "")].copy()


def team_availability_summary(availability_df, week):
    """Return simple team availability summary for selected week."""
    if availability_df is None or availability_df.empty or "Navn" not in availability_df.columns:
        return pd.DataFrame(columns=["Navn", "Status", "Available"])

    rows = []
    for _, row in availability_df.iterrows():
        person = clean(row.get("Navn"))
        if not person:
            continue
        status = availability_status(availability_df, person, week)
        rows.append({
            "Navn": person,
            "Status": status,
            "Available": status not in UNAVAILABLE_STATUSES,
        })
    return pd.DataFrame(rows)
