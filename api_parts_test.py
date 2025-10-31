import requests
import os
import sys
from datetime import date, timedelta
from typing import List, Dict, Set, Optional
import json
from urllib.parse import urlencode
from dotenv import load_dotenv
 
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

    payload = {
        "OrderBy": "Id",
        "SortOrderAscending": 0,
        "PageSize": 100,
        "PageNumber": 1,
        "Criteria": [
            {
                "FieldName": "UserStatus",
                "Operator": "=",
                "Value": "Active"
            }
        ]
    }

    # Make the request
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error fetching firm users: {response.status_code} - {response.text}")
        return 1
    
    firm_json = json.dumps(response.json(), indent=2)
    firm_list = json.loads(firm_json)['FirmUsers']
    
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
                "FieldName": "FirmUserId",
                "Operator": "=",
                "Value": 92915      # My user ID
            },
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

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

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
    # print(firm_users)

    # Testing search timecards
    # start_date = "2025-10-27"
    # end_date = "2025-10-31"
    def get_work_week_dates():
        today = date.today()
    
        # Get Monday of current week (weekday: 0=Monday, 6=Sunday)
        monday = today - timedelta(days=today.weekday())
        
        # Get Friday of current week (Monday + 4 days)
        friday = monday + timedelta(days=4)
        
        return monday.strftime('%Y-%m-%d'), friday.strftime('%Y-%m-%d')

    start_date, end_date = get_work_week_dates()
    search_timecards(access_token, start_date, end_date)

if __name__ == "__main__":
    main()