from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import datetime import date, timedelta
import time
import os
import msal
import json
from dotenv import load_dotenv
 
# Loading environment variables from a .env file
load_dotenv()

# Environment variables for TimeSolv API
# NOTE: I will need to move these parts into production repo, and then call in .yaml
TIMESOLV_CLIENT_ID = os.getenv('TIMESOLV_CLIENT_ID')
TIMESOLV_CLIENT_SECRET = os.getenv('TIMESOLV_CLIENT_SECRET')
TIMESOLV_AUTH_CODE = os.getenv('TIMESOLV_AUTH_CODE')
REDIRECT_URI = os.getenv('REDIRECT_URI')

def get_work_week_dates():
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

def main():
    # Obtain access token
    timesolv_auth = TimeSolveAuth(
        client_id=TIMESOLV_CLIENT_ID,
        client_secret=TIMESOLV_CLIENT_SECRET,
        auth_code=TIMESOLV_AUTH_CODE,
        redirect_uri=REDIRECT_URI
    )
    access_token = timesolv_auth.get_access_token()

    # Initialize TimeSolv API
    timesolv_api = TimeSolvAPI(access_token=access_token)
    
    # Fetch firm users
    firm_users = timesolv_api.get_all_firm_users()

    # TODO: Add logging and error handling as needed
    # if isinstance(firm_users, str):
    #     print(f"Error fetching firm users: {firm_users}")
    # else:
    #     print(f"Fetched {len(firm_users)} firm users.")
    #     for user in firm_users:
    #         print(f"User ID: {user['Id']}, Name: {user['FirstName']} {user['LastName']}")

if __name__ == "__main__":
    main()