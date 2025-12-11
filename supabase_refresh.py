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

# List of user IDs to exclude from email notifications -> see if could implement this dynamically later
exclude_user_ids = [87002]

# Retry number for attempted API calls and such
MAX_RETRIES = 3

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
    previous_work_week_dates = get_previous_work_week_dates()
    logger.info(f"Fetching timecards from {previous_work_week_dates[0]} to {previous_work_week_dates[-1]}...")

    # Create dataframe that contains user ID and dates with submission of timecard for each day
    column_list = ['UserId'] + previous_work_week_dates
    listed_dates_columns = ['UserId', 'NoSubmissionDates', 'NoSubmissionCount', 'lastUpdateDate' , 'Comments']

    timecard_tracker_df = pd.DataFrame(columns=column_list)
    timecard_listed_dates_df = pd.DataFrame(columns=listed_dates_columns)

    # Iterate through firm users and populate dataframe
    failed_users = 0            
    for user in firm_users:
        if user['Id'] in exclude_user_ids:
            logger.info(f"Excluding user {user['Id']} from tracking as per exclusion list.")
            continue

        timecard_row = {'UserId': user['Id']}
        timecard_listed_dates_row = {'UserId': user['Id'], 'Comments': ""}
        timecard_missing_dates = []

        for attempt in range(1, MAX_RETRIES + 1):
            timecards = timesolv_api.search_timecards(
                start_date=previous_work_week_dates[0],
                end_date=previous_work_week_dates[-1],
                firm_user_id=user['Id']
            )

            if isinstance(timecards, List) and (len(timecards) == 0 or isinstance(timecards[0], Dict)):
                logger.info(f"Successfully obtained previous week's timecards for user {user['Id']} on attempt {attempt}.")
                break

            if attempt < MAX_RETRIES:
                logger.warning(f"Attempt {attempt} to get previous week's timecards for user {user['Id']} failed. Retrying...")
                time.sleep(2)

        if isinstance(timecards, str):
            logger.error(f"Error fetching previous week's timecards for user {user['Id']}: {timecards}")
            timecard_listed_dates_row['NoSubmissionDates'] = []
            timecard_listed_dates_row['NoSubmissionCount'] = 0
            timecard_listed_dates_row['Comments'] = f"Error fetching previous week's timecards: {timecards}"
            timecard_listed_dates_df = pd.concat([timecard_listed_dates_df, pd.DataFrame([timecard_listed_dates_row])], ignore_index=True)
            continue

        # Initialize all dates to 0 (no submission)
        for date_str in previous_work_week_dates:
            timecard_row[date_str] = 0

        # Mark dates with submissions as 1
        if not isinstance(timecards, str):
            for tc in timecards:
                tc_date = tc.get('Date')
                if tc_date in timecard_row:
                    timecard_row[tc_date] = 1

        timecard_missing_dates = [date_str for date_str in previous_work_week_dates if timecard_row[date_str] == 0]
        timecard_listed_dates_row['NoSubmissionDates'] = timecard_missing_dates
        timecard_listed_dates_row['NoSubmissionCount'] = len(timecard_missing_dates)

        # Append row to dataframe; update for timesheet fetch from TimeSolv
        timecard_listed_dates_row['lastUpdateDate'] = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')

        timecard_tracker_df = pd.concat([timecard_tracker_df, pd.DataFrame([timecard_row])], ignore_index=True)
        timecard_listed_dates_df = pd.concat([timecard_listed_dates_df, pd.DataFrame([timecard_listed_dates_row])], ignore_index=True)

    logger.info(f"Processed {len(firm_users)} users. {failed_users} failed.")

    # Get Supabase data to update dates
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            supabase = SupabaseAPI()
            logger.info(f"Successfully initialized Supabase client on attempt {attempt}.")
            response = supabase.remove_dates(timecard_listed_dates_df)

            if response.data is not None:
                logger.info(f"Supabase update successful on attempt {attempt}. Updated {len(response.data)} records.")
                break
            else:
                logger.warning(f"Supabase returned None data on attempt {attempt}")
                
                if attempt < MAX_RETRIES:
                    time.sleep(2)
        except Exception as e:
            logger.error(f"Error updating Supabase on attempt {attempt}: {e}")
            
            if attempt < MAX_RETRIES:
                logger.warning(f"Retrying Supabase update...")
                time.sleep(2)
    else:
        logger.error("Exceeded maximum retries for Supabase update. Now exiting process.")
        return

if __name__ == "__main__":
    previous_work_week_dates = get_previous_work_week_dates()
    print("Previous work week dates:", previous_work_week_dates)
    # main()