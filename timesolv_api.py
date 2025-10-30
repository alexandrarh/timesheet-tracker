import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set

class TimeSolvAPI:
    def __init__(self, access_token: str):
        """Initialize the TimeSolvAPI with the provided access token."""
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
    