from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta
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

def get_start_and_end_week_dates():
    """Get the start (Monday) and end (Friday) dates of the current work week.
    
    Returns:
    - Tuple containing start and end dates as strings in 'YYYY-MM-DD' format.
    """
    today = date.today()

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
    today = date.today()
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
        logger.error(f"Failed to obtain access token: {access_token}")  # TODO: Figure out how to restart process (max tries before alert)
        return

    # Initialize TimeSolv API
    timesolv_api = TimeSolvAPI(access_token=access_token)
    
    # Fetch firm users
    firm_users = timesolv_api.get_all_firm_users()
    if isinstance(firm_users, str):
        logger.error(f"Error fetching firm users: {firm_users}")  # TODO: Figure out how to restart process (max tries before alert)
        return

    # Get dates for range (current work week)
    start_date, end_date = get_start_and_end_week_dates()
    logger.info(f"Fetching timecards from {start_date} to {end_date}...")

    # Create dataframe that contains user ID and dates with submission of timecard for each day -> this will be created into XLSX/CSV later
    work_week_dates = get_work_week_dates()
    column_list = ['UserId', 'Email', 'Name'] + work_week_dates
    timecard_tracker_df = pd.DataFrame(columns=column_list)

    # Iterate through firm users and populate dataframe
    for user in firm_users:
        timecard_row = {'UserId': user['Id'], 'Email': user['Email'], 'Name': f"{user['FirstName'].strip()} {user['LastName'].strip()}"}
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

        # Append row to dataframe - convert dict to DataFrame first
        timecard_tracker_df = pd.concat([timecard_tracker_df, pd.DataFrame([timecard_row])], ignore_index=True)

    # Create dictionary containing userId, email, and dates with no submissions
    user_no_submission_dates = {}
    for _, row in timecard_tracker_df.iterrows():
        no_submission_dates = [date for date in work_week_dates if row[date] == 0]
        user_no_submission_dates[row['UserId']] = (row['Email'], row['Name'], no_submission_dates)

    # Check which users have a non-empty list in dictionary
    missing_submission_users = [user_id for user_id, (email, name, dates) in user_no_submission_dates.items() if len(dates) > 0]

    # Draft up email content for users with no submissions 
    email_draft = EmailDraft()
    status, access_token = email_draft.get_access_token()

    if not status:
        logger.error(access_token)      # TODO: Figure out how to restart process (max tries before alert)
        return

    # Sending out emails
    for user_id in missing_submission_users:
        email, sender_name, dates = user_no_submission_dates[user_id]
        status, message = email_draft.send_email(
            token=access_token,
            to_email=email,                                         # NOTE: Format is user_no_submission_dates[user_id][0]
            name=sender_name,                                       # NOTE: Format is user_no_submission_dates[user_id][1]
            start_date=start_date,
            end_date=end_date,
            missing_dates=dates                                     # NOTE: Format is user_no_submission_dates[user_id][2]
        )

        if not status:
            logger.error(message)      # TODO: Figure out how to restart process (max tries before alert)
            return

        logger.info(message)
    
    # NOTE: Output the dataframe to a CSV for record-keeping -> keep in production repo (in file)

    # TODO: Add logging for the error handling here
    # if isinstance(timecards, str):
    #     user_timecard_count[user['Id']] = 0
    # else:
    #     user_timecard_count[user['Id']] = len(timecards)

    # TODO: Add logging and error handling as needed
    # if isinstance(firm_users, str):
    #     print(f"Error fetching firm users: {firm_users}")
    # else:
    #     print(f"Fetched {len(firm_users)} firm users.")
    #     for user in firm_users:
    #         print(f"User ID: {user['Id']}, Name: {user['FirstName']} {user['LastName']}")

    # Fetch timecards for the current work week
    # timecards = timesolv_api.search_timecards(start_date=start_date, end_date=end_date)

if __name__ == "__main__":
    main()