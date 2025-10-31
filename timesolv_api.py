import requests
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import json
from urllib.parse import urlencode

class TimeSolveAuth:
    """Handles OAuth2 authentication for TimeSolv API."""
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_base_url = "https://apps.timesolv.com/App/Authorize.aspx"
        self.token_url = "https://apps.timesolv.com/Services/rest/oAuth2V1/Token"

    def get_authorization_url(self, state: str = "timecard_checker") -> str:
        """Generate the authorization URL for user to approve access."""
        params = {
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "state": state
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def get_access_token(self, auth_code: str) -> str:
        """Exchange authorization code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        result = response.json()
        return result["AccessToken"]

class TimeSolvAPI:
    """API for retrieving necessary TimeSolv timesheet data."""
    def __init__(self, access_token: str):
        self.base_url = "https://api.timesolv.com/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_all_firm_users(self) -> List[Dict]:
        """Fetch all users associated with the firm.
        
        Returns:
        - A list of dictionaries containing user details.
        """
        pass

    def search_timecards(self, start_date: str, end_date: str) -> List[Dict]:
        """Search for timecards within the specified date range.

        Args:
        - start_date (str): The start date for the search (YYYY-MM-DD).
        - end_date (str): The end date for the search (YYYY-MM-DD).

        Returns:
        - A list of dictionaries containing timecard details.
        """
        pass

    def check_timecard_status(self, start_date: str, end_date: str) -> Dict:
        """Checks which employees have submitted timecards for the given range

        Returns:
        - Dictionary containing employee timecard status and information.
        """
        pass
    