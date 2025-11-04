import requests
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('TIMESOLV_CLIENT_ID')
CLIENT_SECRET = os.getenv('TIMESOLV_CLIENT_SECRET')
AUTH_CODE = os.getenv('TIMESOLV_AUTH_CODE')
REDIRECT_URI = os.getenv('REDIRECT_URI')

class TimeSolveAuth:
    """Handles OAuth2 authentication for TimeSolv API."""
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.auth_code = AUTH_CODE
        self.redirect_uri = REDIRECT_URI

    def get_access_token(self) -> str:
        """Exchange authorization code for access token."""
        access_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post('https://apps.timesolv.com/Services/rest/oAuth2V1/Token', data=access_data)
        token_data = response.json()
        access_token = token_data["access_token"]
        
        return access_token

class TimeSolvAPI:
    """API for retrieving necessary TimeSolv timesheet data."""
    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_all_firm_users(self) -> List[Dict] | str:
        """Fetch all users associated with the firm.
        
        Returns:
        - A list of dictionaries containing user details.
        - Error code as string if the request fails.
        """

        url = 'https://apps.timesolv.com/Services/rest/oauth2v1/firmUserSearch'

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
            response = requests.post(url, headers=self.headers, json=payload).json()

            if response.get("ErrorCode"):
                return f"Error fetching firm users: {response['ErrorCode']} - {response['ErrorMessage']}"

            # Extract user information
            users = response.get("FirmUsers", [])
            if not users:
                break

            # Append users to firm list
            firm_list.extend(users)

            if len(users) < page_size:
                break
            
            page_number += 1
            
        return firm_list

    def search_timecards(self, start_date: str, end_date: str, firm_user_id: int) -> List[Dict] | str:
        """Search for timecards within the specified date range.

        Args:
        - start_date (str): The start date for the search (YYYY-MM-DD).
        - end_date (str): The end date for the search (YYYY-MM-DD).
        - firm_user_id (int): The ID of the firm user whose timecards are to be searched.

        Returns:
        - A list of dictionaries containing timecard details.
        """

        url = 'https://apps.timesolv.com/Services/rest/oauth2v1/timecardSearch'
        page_size = 100
        page_number = 1
        timecard_list = []

        while True:
            payload = {
                "Criteria": [
                    {
                        "FieldName": "FirmUserId",
                        "Operator": "=",
                        "Value": firm_user_id
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
                "PageSize": page_size,
                "PageNumber": page_number
            }

            response = requests.post(url, headers=self.headers, json=payload).json()

            if response.get("ErrorCode"):
                return f"Error fetching time cards: {response['ErrorCode']} - {response['ErrorMessage']}"

            timecards = response.get("TimeCards", [])
            if not timecards:
                break

            timecard_list.extend(timecards)
            if len(timecards) < page_size:
                break

            page_number += 1

        return timecard_list