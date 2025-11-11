import requests
import msal
import json
import os
from dotenv import load_dotenv
 
load_dotenv()
CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
TENANT_ID = os.getenv('MICROSOFT_TENANT_ID')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

class EmailDraft:
    def get_access_token(self) -> tuple[bool, str]:
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

        if 'access_token' not in result:
            error = result.get("error")
            error_description = result.get("error_description")
            correlation_id = result.get("correlation_id")
            message = f"Could not obtain access token: {error} - {error_description} (Correlation ID: {correlation_id})"

            return False, message

        return True, result['access_token']

    def send_email(self, token, to_email, name, user_id, start_date, end_date, missing_dates) -> tuple[bool, str]:
        """
        Send an email using Microsoft Graph API.

        Args:
        - token: The access token for Microsoft Graph API.
        - to_email: The recipient's email address.
        - name: The recipient's name.
        - user_id: The recipient's user ID.
        - start_date: Start date of the work week.
        - end_date: End date of the work week.
        - missing_dates: List of dates with missing time sheet submissions.
        """

        body = f"Dear {name},\n\nOur records indicate that you have not submitted your time sheets for the following dates in the current work week:\n"
        for date in missing_dates:
            body += f"- {date}\n"
        body += "\nPlease ensure that you submit your time sheets on TimeSolv at your earliest convenience. Otherwise, the above dates will be processed as PTO; however, if PTO was already requested for the specific dates above, please ignore this email. \n\nIf you have any questions or concerns, please don't hesitate to reach out.\n\nBest regards,\nAlexandra Hernandez"

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
            'saveToSentItems': "false"
        }

        endpoint = f'https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail'
        response = requests.post(endpoint, headers=headers, json=message)
        
        # If there's an error sending the email
        if response.status_code != 202:
            status = False
            message_str = f"Failed to send email. Status code: {response.status_code}"
            return status, message_str
        
        status = True
        message_str = f"Email sent successfully to {user_id}."
        return status, message_str

    def summary_email(self, token, to_email, missing_users_dates, start_date, end_date) -> tuple[bool, str]:
        """
        Send a summary email listing all users with missing time sheet submissions.
        
        Args:
        - token: The access token for Microsoft Graph API.
        - to_email: The recipient's email address, admins.
        - missing_users_dates: A dictionary mapping user IDs to their missing date ranges.
        - start_date: Start date of the work week.
        - end_date: End date of the work week.
        """

        # This will contain a summary report of all users with missing submissions
        body = ""

        subject = "Summary of Users with Missing Time Sheet Submissions for Work Week " + start_date + " to " + end_date

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
            'saveToSentItems': "false"
        }

        endpoint = f'https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail'
        response = requests.post(endpoint, headers=headers, json=message)
        
        # If there's an error sending the email
        if response.status_code != 202:
            status = False
            message_str = f"Failed to send email. Status code: {response.status_code}"
            return status, message_str
        
        status = True
        message_str = f"Email sent successfully to {user_id}."
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