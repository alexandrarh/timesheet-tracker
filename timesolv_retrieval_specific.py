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

def get_work_week_date_range(start_date, end_date) -> List[str] | None:
    """Get the start (Monday) and end (Friday) dates of the current work week.

    Returns:
    - List of dates as strings in 'YYYY-MM-DD' format.
    """
    # Use Eastern time to get the correct "today" regardless of UTC time
    today = datetime.now(ZoneInfo('America/New_York')).date()
    monday = today - timedelta(days=today.weekday())
    
    # Generate all 5 work days
    work_week = [monday + timedelta(days=i) for i in range(5)]
    
    return [day.strftime('%Y-%m-%d') for day in work_week]

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


def main():
    while True:
        print("Welcome to the timecard retrieval tool. Type \"start\" to begin, \"help\" for instructions, or \"exit\" to quit.")
        time.sleep(1) 
        starting_input = input("Enter command: ").strip().lower()

        if starting_input == "start":
            prompt_for_date_range()
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