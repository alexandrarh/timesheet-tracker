from timesolv_api import TimeSolvAPI, TimeSolveAuth
from datetime import date, datetime
from typing import List, Dict
import time
import os
import pandas as pd

# User IDs to exclude from the output entirely
EXCLUDE_USER_IDS = [87002, 97461]

# WIP statuses — timecards not yet put on an invoice
WIP_STATUSES = {"New", "Submitted", "Approved", "Rejected"}

MAX_RETRIES = 3
OUTPUT_FILE = "wip_timecards.xlsx"


def prompt_for_date_range() -> tuple[str, str]:
    """Prompt the user for a valid start and end date range."""
    today = date.today().strftime("%Y-%m-%d")
    while True:
        start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter the end date (YYYY-MM-DD): ").strip()

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD. Example: 2024-06-01\n")
            continue

        if start_date > end_date:
            print("Start date cannot be after end date.\n")
        elif start_date > today or end_date > today:
            print("Dates cannot be in the future.\n")
        else:
            print(f"Date range confirmed: {start_date} to {end_date}\n")
            return start_date, end_date


def fetch_with_retry(label: str, fn, *args):
    """Call fn(*args), retrying up to MAX_RETRIES times on failure."""
    result = None
    for attempt in range(1, MAX_RETRIES + 1):
        result = fn(*args)
        if isinstance(result, list):
            print(f"Successfully obtained {label} on attempt {attempt} ({len(result)} records).")
            return result
        if attempt < MAX_RETRIES:
            print(f"Attempt {attempt} to get {label} failed. Retrying...")
            time.sleep(2)
    print(f"Failed to obtain {label} after {MAX_RETRIES} attempts: {result}")
    return None


def main():
    while True:
        print('Type "start" to begin, "help" for instructions, or "exit" to quit.')
        cmd = input("Enter command: ").strip().lower()

        if cmd == "start":
            start_date, end_date = prompt_for_date_range()
            run(start_date, end_date)
            break
        elif cmd == "help":
            print(
                "Instructions:\n"
                "  - Enter 'start' to begin retrieving WIP timecards.\n"
                "  - You will be prompted for a start and end date (YYYY-MM-DD).\n"
                "  - End date must be on or after start date.\n"
                "  - Both dates must be today or in the past.\n"
            )
        elif cmd in ("exit", "quit"):
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid command. Please try again.\n")


def run(start_date: str, end_date: str):
    # --- Auth ---
    auth = TimeSolveAuth()
    status = False
    access_token = None
    for attempt in range(1, MAX_RETRIES + 1):
        status, access_token = auth.get_access_token()
        if status:
            print(f"Successfully obtained access token on attempt {attempt}.")
            break
        if attempt < MAX_RETRIES:
            print(f"Attempt {attempt} to get access token failed. Retrying...")
            time.sleep(2)
    if not status:
        print(f"{access_token}. Exceeded maximum retries. Exiting.")
        return

    timesolv_api = TimeSolvAPI(access_token=access_token)

    # --- Fetch supporting data for lookups ---
    firm_users = fetch_with_retry("firm users", timesolv_api.get_all_firm_users)
    if firm_users is None:
        return

    client_list = fetch_with_retry("clients", timesolv_api.get_client_details)
    if client_list is None:
        return

    project_summaries = fetch_with_retry("project summaries", timesolv_api.get_project_summaries)
    if project_summaries is None:
        return

    projects = fetch_with_retry("projects", timesolv_api.get_project_details)
    if projects is None:
        return

    # --- Build lookups ---

    # External ClientId string -> client dict
    client_lookup: Dict[str, Dict] = {
        str(c.get("ClientId", "")).strip(): c
        for c in client_list
        if str(c.get("ClientId", "")).strip()
    }

    # Project internal Id -> project summary (for ClientProjectId)
    project_summary_lookup: Dict[int, Dict] = {
        p["Id"]: p for p in project_summaries
    }

    # Project internal Id -> project detail (for ProjectName, external ProjectId)
    project_detail_lookup: Dict[int, Dict] = {
        p["Id"]: p for p in projects
    }

    # --- Remove the output file if it already exists so we start fresh ---
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    # --- Per-user timecard fetch and sheet write ---
    failed_users = []
    written_users = 0

    for user in firm_users:
        if user["Id"] in EXCLUDE_USER_IDS:
            print(f"Skipping excluded user {user['Id']}.")
            continue

        employee_name = f"{user.get('FirstName', '')} {user.get('LastName', '')}".strip()
        sheet_name = employee_name[:31]  # Excel sheet names are capped at 31 characters

        # Fetch timecards for this user within the date range
        timecards = None
        for attempt in range(1, MAX_RETRIES + 1):
            timecards = timesolv_api.search_timecards(
                start_date=start_date,
                end_date=end_date,
                firm_user_id=user["Id"]
            )
            if isinstance(timecards, list):
                print(f"Got {len(timecards)} timecard(s) for {employee_name} on attempt {attempt}.")
                break
            if attempt < MAX_RETRIES:
                print(f"Attempt {attempt} to get timecards for {employee_name} failed. Retrying...")
                time.sleep(2)
        if not isinstance(timecards, list):
            print(f"Error fetching timecards for {employee_name}: {timecards}")
            failed_users.append(employee_name)
            continue

        # Filter to WIP statuses only (client-side, since the API only supports AND between criteria)
        wip_timecards = [
            tc for tc in timecards
            if tc.get("TimeCardStatus") in WIP_STATUSES
        ]

        # Build rows — initialized once before the loop, appended to throughout
        rows = []
        for tc in wip_timecards:
            project_internal_id = tc.get("ProjectId")
            summary = project_summary_lookup.get(project_internal_id, {})
            detail = project_detail_lookup.get(project_internal_id, {})

            client_key = summary.get("ClientProjectId", "").split(" - ", 1)[0].strip()
            client = client_lookup.get(client_key, {})

            rows.append({
                "Date":           tc.get("Date"),
                "EmployeeName":   employee_name,
                "ClientName":     client.get("ClientName", ""),
                "ClientId":       client.get("ClientId", ""),
                "ProjectName":    detail.get("ProjectName", ""),
                "ProjectId":      detail.get("ProjectId", ""),
                "BillableStatus": tc.get("BillableStatus"),
                "TimeCardStatus": tc.get("TimeCardStatus"),
                "Duration":       tc.get("Duration"),
                "TotalAmount":    tc.get("TotalAmount"),
                "Notes":          tc.get("Notes"),
            })

        employee_df = pd.DataFrame(
            rows,
            columns=[
                "Date", "EmployeeName", "ClientName", "ClientId",
                "ProjectName", "ProjectId", "BillableStatus", "TimeCardStatus",
                "Duration", "TotalAmount", "Notes",
            ]
        )

        # Write sheet — 'w' on first user to create the file, 'a' thereafter to append
        if os.path.exists(OUTPUT_FILE):
            writer_kwargs = {"engine": "openpyxl", "mode": "a", "if_sheet_exists": "replace"}
        else:
            writer_kwargs = {"engine": "openpyxl", "mode": "w"}

        with pd.ExcelWriter(OUTPUT_FILE, **writer_kwargs) as writer:
            employee_df.to_excel(writer, sheet_name=sheet_name, index=False)

        written_users += 1

    print(
        f"\nDone. WIP timecards written for {written_users} employee(s) "
        f"to '{OUTPUT_FILE}'."
    )
    if failed_users:
        print(f"Failed to retrieve timecards for: {failed_users}")


if __name__ == "__main__":
    main()