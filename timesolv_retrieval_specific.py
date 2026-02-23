from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from typing import List, Dict
import time
import os
import pandas as pd

# List of user IDs to exclude from email notifications -> see if could implement this dynamically later
exclude_user_ids = [87002]

# Retry number for attempted API calls and such
MAX_RETRIES = 3

def get_work_week_date_range(start_date: str, end_date: str) -> List[str] | None:
    """Get all working days (Monday–Friday) within the given date range

    Args:
        start_date: Start date string in 'YYYY-MM-DD' format.
        end_date: End date string in 'YYYY-MM-DD' format.

    Returns:
        List of working day dates as strings in 'YYYY-MM-DD' format, or None if invalid.
    """
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Collect all weekdays (Mon–Fri) between start and end inclusive
    work_days = [
        start + timedelta(days=i)
        for i in range((end - start).days + 1)
        if (start + timedelta(days=i)).weekday() < 5  # 0=Mon, 4=Fri
    ]

    return [day.strftime('%Y-%m-%d') for day in work_days] if work_days else None

def prompt_for_date_range():
    while True:
        start_date = input("Enter the start date (YYYY-MM-DD): ")
        end_date = input("Enter the end date (YYYY-MM-DD): ")

        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD. Example: 2024-06-01\n")
            continue

        if start_date > end_date:
            print("Start date cannot be after end date.\n")
        elif start_date > date.today().strftime('%Y-%m-%d') or end_date > date.today().strftime('%Y-%m-%d'):
            print("Start date and end date cannot be in the future.\n")
        else:
            break

    print(f"Date range is valid: {start_date} to {end_date}")
    work_week_dates = get_work_week_date_range(start_date, end_date)
    return work_week_dates

def main_process(work_week_dates: List[str]):
    # Initialize TimeSolv API client
    auth = TimeSolveAuth()
    for attempt in range(1, MAX_RETRIES + 1):
        status, access_token = auth.get_access_token()

        # Breaking with successful access token retrieval
        if status:
            print(f"Successfully obtained TimeSolv access token on attempt {attempt}.")
            break

        if attempt < MAX_RETRIES:
            print(f"Attempt {attempt} to get TimeSolv access token failed. Retrying...")
            time.sleep(2)  
    if not status:
        print(f"{access_token}. Exceeded maximum retries. Now exiting process.")
        return
    
    # Initialize TimeSolv API and fetch firm users with retry logic
    timesolv_api = TimeSolvAPI(access_token=access_token)
    for attempt in range(1, MAX_RETRIES + 1):
        firm_users = timesolv_api.get_all_firm_users()

        # Breaking with successful firm users retrieval
        if isinstance(firm_users, List) and isinstance(firm_users[0], Dict):
            print(f"Successfully obtained firm users on attempt {attempt}.")
            break

        if attempt < MAX_RETRIES:
            print(f"Attempt {attempt} to get firm users failed. Retrying...")
            time.sleep(2)  
    if isinstance(firm_users, str):
        print(f"{firm_users}. Exceeded maximum retries. Now exiting process.")
        return

def main():
    while True:
        print("Welcome to the timecard retrieval tool. Type \"start\" to begin, \"help\" for instructions, or \"exit\" to quit.")
        time.sleep(1) 
        starting_input = input("Enter command: ").strip().lower()

        if starting_input == "start":
            work_week_dates = prompt_for_date_range()
            main_process(work_week_dates)
            break
        elif starting_input == "help":
            print("Instructions for using the timecard retrieval tool:")
            print("- Enter \"start\" to begin retrieving timecards.")
            print("- You will be prompted to enter a start and end date.")
            print("- The dates must be in YYYY-MM-DD format.")
            print("- The end date must be on or after the start date.")
            print("- The dates must be in the past or today's date. \n")
            continue
        elif starting_input == "exit" or starting_input == "quit":
            print("Exiting the tool. Goodbye!")
            break
        else:
            print("Invalid command. Please try again. \n")
            continue

if __name__ == "__main__":
    main()