import requests
import os
import sys
from datetime import date, timedelta
from typing import List, Dict, Set, Optional
import json
from urllib.parse import urlencode
from dotenv import load_dotenv
import pandas as pd
 
# Loading environment variables from a .env file
load_dotenv()

# Environment variables for TimeSolv API
TIMESOLV_CLIENT_ID = os.getenv('TIMESOLV_CLIENT_ID')
TIMESOLV_CLIENT_SECRET = os.getenv('TIMESOLV_CLIENT_SECRET')
TIMESOLV_AUTH_CODE = os.getenv('TIMESOLV_AUTH_CODE')
REDIRECT_URI = os.getenv('REDIRECT_URI')

def get_access_token(access_data: Dict) -> str:
    """Obtain access token from TimeSolv API using authorization code."""
    response = requests.post('https://apps.timesolv.com/Services/rest/oAuth2V1/Token', data=access_data)
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return access_token

def get_firm_users(access_token: str) -> List[Dict] | int:
    """Fetch all users associated with the firm."""
    access_token = access_token
    url = 'https://apps.timesolv.com/Services/rest/oauth2v1/firmUserSearch'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    firm_list = []
    page_size = 100
    page_number = 1

    # Loop to go thru pages
    while True:
        # Payload to fetch active users
        payload = {
            "OrderBy": "Id",
            "SortOrderAscending": 0,
            "PageSize": page_size,
            "PageNumber": page_number,
            "Criteria": [
                {
                    "FieldName": "UserStatus",
                    "Operator": "=",
                    "Value": "Active"
                }
            ]
        }

        # Make the request
        response = requests.post(url, headers=headers, json=payload).json()

        if response.get("ErrorCode"):
            return f"Error fetching firm users: {response['ErrorCode']} - {response['ErrorMessage']}"

        users = response.get("FirmUsers", [])
        if not users:
            break

        firm_list.extend(users)

        if len(users) < page_size:
            break
        
        page_number += 1
        
    return firm_list

    # Check the result
    # print(f"Status Code: {response.status_code}")
    # print(f"Response: {json.dumps(response.json(), indent=2)}")

# List[Dict] | int
# start_date: str, end_date: str
def search_timecards(access_token: str, start_date: str, end_date: str):
    """Search timecards within a specified date range."""
    url = 'https://apps.timesolv.com/Services/rest/oauth2v1/timecardSearch'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        "Criteria": [
            {
                "FieldName": "Date",
                "Operator": ">=",
                "Value": start_date
            },
            {
                "FieldName": "Date",
                "Operator": "<=",
                "Value": end_date
            }
        ],
        "OrderBy": "Date",
        "SortOrderAscending": 1,
        "PageSize": 1000,
        "PageNumber": 1
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error fetching time cards: {response.status_code} - {response.text}")
        return 1
    
    timecard_json = json.dumps(response.json(), indent=2)
    timecard_list = json.loads(timecard_json)['TimeCards']

    return timecard_list

def main():
    access_data = {
        "client_id": TIMESOLV_CLIENT_ID,
        "client_secret": TIMESOLV_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": TIMESOLV_AUTH_CODE,
        "redirect_uri": REDIRECT_URI
    }

    access_token = get_access_token(access_data)
    # print(f"Access Token: {access_token}")

    # Testing get all firm users
    firm_users = get_firm_users(access_token)
    firm_list = []
    for user in firm_users:
        if user['Id'] == 87002:
            continue

        firm_list.append({
            "UserId": user['Id'],
            "Email": user['Email'],
            "FirstName": user['FirstName'].strip(),
            "LastName": user['LastName'].strip(),
            "UserStatus": user['UserStatus'],
            "EmploymentStatus": user['EmploymentStatus'],
            "LastUpdated": user['LastUpdatedDate']
        })

    firm_df = pd.DataFrame(firm_list)
    print(firm_df)
    firm_df.to_csv('firm_users.csv', index=False)

    # Testing search timecards
    # def get_start_and_end_week_dates():
    #     """Get the start (Monday) and end (Friday) dates of the current work week.
        
    #     Returns:
    #     - Tuple containing start and end dates as strings in 'YYYY-MM-DD' format.
    #     """
    #     today = date.today()

    #     # Get Monday of current week (weekday: 0=Monday, 6=Sunday)
    #     monday = today - timedelta(days=today.weekday())
        
    #     # Get Friday of current week (Monday + 4 days)
    #     friday = monday + timedelta(days=4)
        
    #     return monday.strftime('%Y-%m-%d'), friday.strftime('%Y-%m-%d')

    # def get_work_week_dates():
    #     """Get the start (Monday) and end (Friday) dates of the current work week.

    #     Returns:
    #     - List of dates as strings in 'YYYY-MM-DD' format.
    #     """
    #     today = date.today()
    #     monday = today - timedelta(days=today.weekday())
        
    #     # Generate all 5 work days
    #     work_week = [monday + timedelta(days=i) for i in range(5)]
        
    #     return [day.strftime('%Y-%m-%d') for day in work_week]

    # print("Current Work Week Dates:", get_work_week_dates())
    # column_list = ['UserId'] + get_work_week_dates()
    # print("Column List:", column_list)

    # start_date, end_date = get_work_week_dates()
    # timecards = search_timecards(access_token, start_date, end_date)
    # print(timecards)

if __name__ == "__main__":
    main()