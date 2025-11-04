import requests
import msal
import json
import os
from dotenv import load_dotenv
 
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

class EmailDraft:
    def get_access_token() -> bool, str:
        """Authenticate with Microsoft Graph API to get token."""
        authority = f"https://login.microsoftonline.com/{TENANT_ID}"

        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=authority,
            client_credential=CLIENT_SECRET
        )
        
        # Request token with Mail.Send scope
        result = app.acquire_token_for_client(
            scopes=['https://graph.microsoft.com/.default']
        )
        
        if 'access_token' in result:
            status = True
            return status, result['access_token']
        else:
            status = False
            return status, f"Could not obtain access token: {result.get('error_description')}"

    # TODO: Adjust function for including dates
    def send_email(token, to_email, name, start_date, end_date, missing_dates) -> bool, str:
        """
        Send an email using Microsoft Graph API.

        Args:
        - token: The access token for Microsoft Graph API.
        - to_email: The recipient's email address.
        - missing_dates: List of dates with missing time sheet submissions.
        """

        body = f"Dear {name},\n\nOur records indicate that you have not submitted your time sheets for the following dates in the current work week:\n"
        for date in missing_dates:
            body += f"- {date}\n"
        body += "\nPlease ensure that you submit your time sheets on TimeSolv at your earliest convenience. Otherwise, the selected dates will be processed as PTO.\n\nBest regards,\nAlexandra Hernandez"

        subject = f"Missing time sheets for work week {start_date} to {end_date}"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # For single or multiple recipients
        if isinstance(to_email, str):
            to_recipients = [{"emailAddress": {"address": to_email}}]
        else:
            to_recipients = [{"emailAddress":{"address":email}} for email in to_email]
            
        message = {
            'message': {
                'subject': subject,
                'body': {
                    'contentType': 'Text',
                    'content': body
                },
                'toRecipients': to_recipients
            },
            'saveToSentItems': 'true'
        }

        endpoint = f'https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail'
        
        response = requests.post(endpoint, headers=headers, json=message)
        
        if response.status_code == 202:
            status = True
            message_str = f"Email sent successfully to {to_email}"
            return status, message_str
        else:
            status = False
            message_str = f"Failed to send email. Status code: {response.status_code}"
            return status, message_str

# def main():
#     token = EmailDraft.get_access_token()
#     send_email = EmailDraft.send_email(
#         token=token,
#         to_email=SENDER_EMAIL,
#         name='Jane Doe',
#         start_date='2025-10-27',
#         end_date='2025-10-31',
#         missing_dates=['2025-10-28', '2025-10-29']  # Example dates
#     )

# if __name__ == "__main__":
#     main()