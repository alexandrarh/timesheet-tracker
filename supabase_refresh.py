from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from typing import List, Dict
import time
import os
import pandas as pd
from dotenv import load_dotenv
import ast
from supabase_api import SupabaseAPI

# Setting up logging for the script
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "supabase_refresh_status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

# This file will be dedicated to refreshing data in Supabase from TimeSolv
# Will check if any users have not submitted timesheets for the past week -> if so, remove dates from Supabase, and update count
# Will also run as a separate automation independent of the original timesheet_tracker.py script -> will run weekly on Saturday or Sunday (start of week or end of week)

# Eastern time, regardless of UTC
CURRENT_DATE = datetime.now(ZoneInfo('America/New_York')).date()

def get_work_week_dates():
    """
    Get the start (Monday) and end (Friday) dates of the current work week.

    Returns:
    - List of dates as strings in 'YYYY-MM-DD' format.
    """
    # Use Eastern time to get the correct "today" regardless of UTC time
    today = CURRENT_DATE
    monday = today - timedelta(days=today.weekday())
    
    # Generate all 5 work days
    work_week = [monday + timedelta(days=i) for i in range(5)]
    
    return [day.strftime('%Y-%m-%d') for day in work_week]

# TODO: Check if type is correct
def get_previous_work_week_dates() -> List[str]:
    """
    Get the start (Monday) and end (Friday) dates of the previous work week.

    Returns:
    - List of dates as strings in 'YYYY-MM-DD' format.
    """
    today = CURRENT_DATE
    current_monday = today - timedelta(days=today.weekday())
    
    # Get Monday of previous week (7 days before current Monday)
    previous_monday = current_monday - timedelta(days=7)
    
    # Generate all 5 work days
    previous_work_week = [previous_monday + timedelta(days=i) for i in range(5)]
    
    return [day.strftime('%Y-%m-%d') for day in previous_work_week]

def main():
    logger.info("Starting Supabase refresh process.")

    # Obtain access token
    timesolv_auth = TimeSolveAuth()
    for attempt in range(1, MAX_RETRIES + 1):
        status, access_token = timesolv_auth.get_access_token()

        # Breaking with successful access token retrieval
        if status:
            logger.info(f"Successfully obtained TimeSolv access token on attempt {attempt}.")
            break

        if attempt < MAX_RETRIES:
            logger.warning(f"Attempt {attempt} to get TimeSolv access token failed. Retrying...")
            time.sleep(2)  
    if not status:
        logger.error(f"{access_token}. Exceeded maximum retries. Now exiting process.")
        return

    # Initialize TimeSolv API
    timesolv_api = TimeSolvAPI(access_token=access_token)

    # Fetch firm users
    for attempt in range(1, MAX_RETRIES + 1):
        firm_users = timesolv_api.get_all_firm_users()

        # Breaking with successful firm users retrieval
        if isinstance(firm_users, List) and isinstance(firm_users[0], Dict):
            logger.info(f"Successfully obtained firm users on attempt {attempt}.")
            break

        if attempt < MAX_RETRIES:
            logger.warning(f"Attempt {attempt} to get firm users failed. Retrying...")
            time.sleep(2)  
    if isinstance(firm_users, str):
        logger.error(f"{firm_users}. Exceeded maximum retries. Now exiting process.")
        return

    # Get dates for range (previous work week)
    previous_work_week = get_previous_work_week_dates()
    logger.info(f"Fetching timecards from {previous_work_week[0]} to {previous_work_week[-1]}...")

if __name__ == "__main__":
    main()