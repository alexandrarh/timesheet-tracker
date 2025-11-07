from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Set, Optional
import time
import os
import json
import pandas as pd
from email_draft import EmailDraft

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

# List of user IDs to exclude from email notifications -> see if could implement this dynamically later
exclude_user_ids = [87002, 30847]

# Retry number for attempted API calls and such
MAX_RETRIES = 3

def get_start_and_end_week_dates():
    """Get the start (Monday) and end (Friday) dates of the current work week.
    
    Returns:
    - Tuple containing start and end dates as strings in 'YYYY-MM-DD' format.
    """
    # Use Eastern time to get the correct "today" regardless of UTC time
    today = datetime.now(ZoneInfo('America/New_York')).date()

    # Get Monday of current week (weekday: 0=Monday, 6=Sunday)
    monday = today - timedelta(days=today.weekday())
    
    # Get Friday of current week (Monday + 4 days)
    friday = monday + timedelta(days=4)
    
    return monday.strftime('%Y-%m-%d'), friday.strftime('%Y-%m-%d')

def get_work_week_dates():
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

def main():
    logger.info("Starting main process...")

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

    # Get dates for range (current work week)
    start_date, end_date = get_start_and_end_week_dates()
    logger.info(f"Fetching timecards from {start_date} to {end_date}...")

    # Create dataframe that contains user ID and dates with submission of timecard for each day -> this will be created into XLSX/CSV later
    basic_columns = ['UserId', 'Email', 'Name']
    work_week_dates = get_work_week_dates()
    column_list = basic_columns + work_week_dates
    listed_dates_columns = basic_columns + ['NoSubmissionDates', 'lastEmailSentDate', 'lastUpdateDate', 'Comments']

    timecard_tracker_df = pd.DataFrame(columns=column_list)
    timecard_listed_dates_df = pd.DataFrame(columns=listed_dates_columns)

    # Iterate through firm users and populate dataframe
    failed_users = 0            # Tracking how many users failed to get timecards retrieved
    for user in firm_users:
        if user['Id'] in exclude_user_ids:
            logger.info(f"Excluding user {user['Id']} from tracking as per exclusion list.")
            continue

        timecard_row = {'UserId': user['Id'], 'Email': user['Email'], 'Name': f"{user['FirstName'].strip()} {user['LastName'].strip()}"}
        timecard_listed_dates_row = {'UserId': user['Id'], 'Email': user['Email'], 'Name': f"{user['FirstName'].strip()} {user['LastName'].strip()}", 'Comments': ""}
        timecard_missing_dates = []

        for attempt in range(1, MAX_RETRIES + 1):
            timecards = timesolv_api.search_timecards(
                start_date=start_date,
                end_date=end_date,
                firm_user_id=user['Id']
            )

            if isinstance(timecards, List) and (len(timecards) == 0 or isinstance(timecards[0], Dict)):
                logger.info(f"Successfully obtained timecards for user {user['Id']} on attempt {attempt}.")
                break

            if attempt < MAX_RETRIES:
                logger.warning(f"Attempt {attempt} to get timecards for user {user['Id']} failed. Retrying...")
                time.sleep(2)

        if isinstance(timecards, str):
            logger.error(f"Error fetching timecards for user {user['Id']}: {timecards}")
            timecard_listed_dates_row['NoSubmissionDates'] = []
            timecard_listed_dates_row['Comments'] = timecards
            timecard_listed_dates_df = pd.concat([timecard_listed_dates_df, pd.DataFrame([timecard_listed_dates_row])], ignore_index=True)
            continue

        # Initialize all dates to 0 (no submission)
        for date_str in work_week_dates:
            timecard_row[date_str] = 0

        # Mark dates with submissions as 1
        if not isinstance(timecards, str):
            for tc in timecards:
                tc_date = tc.get('Date')
                if tc_date in timecard_row:
                    timecard_row[tc_date] = 1

        timecard_missing_dates = [date_str for date_str in work_week_dates if timecard_row[date_str] == 0]
        timecard_listed_dates_row['NoSubmissionDates'] = timecard_missing_dates

        # Append row to dataframe - convert dict to DataFrame first
        timecard_tracker_df = pd.concat([timecard_tracker_df, pd.DataFrame([timecard_row])], ignore_index=True)
        timecard_listed_dates_df = pd.concat([timecard_listed_dates_df, pd.DataFrame([timecard_listed_dates_row])], ignore_index=True)

    logger.info(f"Processed {len(firm_users)} users. {failed_users} failed.")

    # Draft up email content for users with no submissions 
    email_draft = EmailDraft()
    for attempt in range(1, MAX_RETRIES + 1):
        status, access_token = email_draft.get_access_token()

        if status:
            logger.info(f"Successfully obtained Microsoft Graph access token on attempt {attempt}.")
            break
        if attempt < MAX_RETRIES:
            logger.warning(f"Attempt {attempt} to get Microsoft Graph access token failed. Retrying...")
            time.sleep(2)
    if not status:
        logger.error(f"{access_token}. Exceeded maximum retries. Now exiting process.")      
        return

    for index, row in timecard_listed_dates_df.iterrows():
        user_id, email, sender_name, dates = row['UserId'], row['Email'], row['Name'], row['NoSubmissionDates']
        
        # Skips sending email if no missing dates and comments exist -> indicates prior error
        if not dates and row['Comments'] != "":
            timecard_listed_dates_df.at[index, 'lastUpdateDate'] = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
            continue

        for attempt in range(1, MAX_RETRIES + 1):
            status, message = email_draft.send_email(
                token=access_token,
                to_email=email,                                         
                name=sender_name,                                       
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                missing_dates=dates
            )

            if status:
                logger.info(f"Successfully sent email to user {user_id} on attempt {attempt}.")
                break

            if attempt < MAX_RETRIES:
                logger.warning(f"Attempt {attempt} to send email to user {user_id} failed. Retrying...")
                time.sleep(2)
        
        if not status:
            logger.error(f"Failed to send email to user {user_id}: {message}. Exceeded maximum retries.")
            timecard_listed_dates_df.at[index, 'lastUpdateDate'] = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
            continue

        logger.info(message)

        # Updating the last email sent and update date columns
        timecard_listed_dates_df.at[index, 'lastEmailSentDate'] = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
        timecard_listed_dates_df.at[index, 'lastUpdateDate'] = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')

    # NOTE: Should there be a generated summary report df, then it's appended to existing data?
    # Database with these collections: user information (e.g. id, name, email), dates with no submission 
    # Dates with no submission: user_id, dates (lists of dates with no submission) -> How do we want to update this when dates are filled in later?
    # Probably will need to build a checker bot that checks for filled-in dates and updates the database accordingly
    
    # Output the dataframe to a CSV for record-keeping -> keep in production repo (in file) -> should be keep emails in or no
    saved_data = timecard_listed_dates_df.drop(['Email', 'Name'], axis=1)
    csv_filename = f"artifacts/timecard_submissions_{start_date}_to_{end_date}.csv"
    saved_data.to_csv(csv_filename, index=False)
    logger.info(f"Timecard submission data saved to {csv_filename}")

if __name__ == "__main__":
    main()