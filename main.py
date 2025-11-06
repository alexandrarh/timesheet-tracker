from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
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
exclude_user_ids = [87002]  

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
    status, access_token = timesolv_auth.get_access_token()
    if not status:
        logger.error(access_token)          # TODO: Figure out how to restart process (max tries before alert)
        return

    # Initialize TimeSolv API
    timesolv_api = TimeSolvAPI(access_token=access_token)
    
    # Fetch firm users
    firm_users = timesolv_api.get_all_firm_users()
    if isinstance(firm_users, str):
        logger.error(firm_users)            # TODO: Figure out how to restart process (max tries before alert)
        return

    # Get dates for range (current work week)
    start_date, end_date = get_start_and_end_week_dates()
    logger.info(f"Fetching timecards from {start_date} to {end_date}...")

    # Create dataframe that contains user ID and dates with submission of timecard for each day -> this will be created into XLSX/CSV later
    basic_columns = ['UserId', 'Email', 'Name']
    work_week_dates = get_work_week_dates()
    column_list = basic_columns + work_week_dates
    listed_dates_columns = basic_columns + ['NoSubmissionDates']

    timecard_tracker_df = pd.DataFrame(columns=column_list)
    timecard_listed_dates_df = pd.DataFrame(columns=listed_dates_columns)

    # Iterate through firm users and populate dataframe
    for user in firm_users:
        if user['Id'] in exclude_user_ids:
            logger.info(f"Excluding user {user['Id']} from tracking as per exclusion list.")
            continue
        timecard_row = {'UserId': user['Id'], 'Email': user['Email'], 'Name': f"{user['FirstName'].strip()} {user['LastName'].strip()}"}
        timecard_listed_dates_row = {'UserId': user['Id'], 'Email': user['Email'], 'Name': f"{user['FirstName'].strip()} {user['LastName'].strip()}"}
        timecard_missing_dates = []

        timecards = timesolv_api.search_timecards(
            start_date=start_date,
            end_date=end_date,
            firm_user_id=user['Id']
        )

        if isinstance(timecards, str):
            logger.error(f"Error fetching timecards for user {user['Id']}: {timecards}")  # TODO: Figure out how to restart process (max tries before alert)
            return

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

    # Draft up email content for users with no submissions 
    email_draft = EmailDraft()
    status, access_token = email_draft.get_access_token()

    if not status:
        logger.error(access_token)      # TODO: Figure out how to restart process (max tries before alert)
        return

    for index, row in timecard_listed_dates_df.iterrows():
        user_id, email, sender_name, dates = row['UserId'], row['Email'], row['Name'], row['NoSubmissionDates']
        status, message = email_draft.send_email(
            token=access_token,
            to_email=email,                                         
            name=sender_name,                                       
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            missing_dates=dates
        )

        if not status:
            logger.error(message)      # TODO: Figure out how to restart process (max tries before alert)
            return

        logger.info(message)

    # NOTE: Should there be a generated summary report df, then it's appended to existing data?
    # Database with these collections: user information (e.g. id, name, email), dates with no submission 
    # Dates with no submission: user_id, dates (lists of dates with no submission) -> How do we want to update this when dates are filled in later?
    # Probably will need to build a checker bot that checks for filled-in dates and updates the database accordingly
    
    # Output the dataframe to a CSV for record-keeping -> keep in production repo (in file) -> should be keep emails in or no
    saved_data = timecard_tracker_df.drop(['Email', 'Name'], axis=1)
    csv_filename = f"artifacts/timecard_submissions_{start_date}_to_{end_date}.csv"
    saved_data.to_csv(csv_filename, index=False)
    logger.info(f"Timecard submission data saved to {csv_filename}")

if __name__ == "__main__":
    main()