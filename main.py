from timesolv_api import TimeSolvAPI, TimeSolveAuth
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import time
from dotenv import load_dotenv
 
# Loading environment variables from a .env file
load_dotenv()

# Environment variables for TimeSolv API
TIMESOLV_CLIENT_ID = os.getenv('TIMESOLV_CLIENT_ID')
TIMESOLV_CLIENT_SECRET = os.getenv('TIMESOLV_CLIENT_SECRET')
TIMESOLV_AUTH_CODE = os.getenv('TIMESOLV_AUTH_CODE')
REDIRECT_URI = os.getenv('REDIRECT_URI')

def main():
    pass

if __name__ == "__main__":
    main()