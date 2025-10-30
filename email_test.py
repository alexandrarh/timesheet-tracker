import requests
import msal
import json
import os
from dotenv import load_dotenv
 
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')

SENDER_EMAIL = 'ah@mcnulty.cpa'