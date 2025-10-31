import requests
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
from urllib.parse import urlencode

class TimeSolveAuth:
    """Handles OAuth2 authentication for TimeSolv API."""
    def __init__(self, client_id: str, client_secret: str, auth_code: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = auth_code
        self.redirect_uri = redirect_uri

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
        self.page_size = 100
        self.page_number = 1
        self.sort_asc = 0
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

        # Payload to fetch active users
        payload = {
            "OrderBy": "Id",
            "SortOrderAscending": self.sort_asc,
            "PageSize": self.page_size,
            "PageNumber": self.page_number,
            "Criteria": [
                {
                    "FieldName": "UserStatus",
                    "Operator": "=",
                    "Value": "Active"
                }
            ]
        }

        # Make the request
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            return f"Error fetching firm users: {response.status_code} - {response.text}"
        
        firm_json = json.dumps(response.json(), indent=2)
        firm_list = json.loads(firm_json)['FirmUsers']
        
        return firm_list

    def search_timecards(self, start_date: str, end_date: str) -> List[Dict] | str:
        """Search for timecards within the specified date range.

        Args:
        - start_date (str): The start date for the search (YYYY-MM-DD).
        - end_date (str): The end date for the search (YYYY-MM-DD).

        Returns:
        - A list of dictionaries containing timecard details.
        """

        url = 'https://apps.timesolv.com/Services/rest/oauth2v1/timecardSearch'

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
            "PageSize": self.page_size,
            "PageNumber": self.page_number
        }

        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code != 200:
            return f"Error fetching time cards: {response.status_code} - {response.text}"
        
        timecard_json = json.dumps(response.json(), indent=2)
        timecard_list = json.loads(timecard_json)['TimeCards']

        return timecard_list

    def check_timecard_status(self, start_date: str, end_date: str) -> Dict:
        """Checks which employees have submitted timecards for the given range

        Returns:
        - Dictionary containing employee timecard status and information.
        """
        pass
    