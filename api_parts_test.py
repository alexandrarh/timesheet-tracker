import requests
import os
import sys
from datetime import datetime, timedelta
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

if __name__ == "__main__":
    main()