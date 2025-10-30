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

def get_access_token():
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
        return result['access_token']
    else:
        raise Exception(f"Could not obtain access token: {result.get('error_description')}")

def send_email(to_email, subject, body, body_type='Text'):
    """
    Send an email using Microsoft Graph API.

    Args:
        to_email: The recipient's email address.
        subject: The subject of the email.
        body: The body content of the email.
        body_type: The type of the body content. Defaults to 'Text'.
    """

    token = get_access_token()

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
                'contentType': body_type,
                'content': body
            },
            'toRecipients': to_recipients
        },
        'saveToSentItems': 'true'
    }

    endpoint = f'https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail'
    
    response = requests.post(endpoint, headers=headers, json=message)
    
    if response.status_code == 202:
        print(f"Email sent successfully to {to_email}")
        return True
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    # print(CLIENT_ID)
    send_email(
        to_email='ah@mcnulty.cpa',
        subject='Test Email',
        body='This is a test email sent from the Microsoft Graph API.'
    )

if __name__ == "__main__":
    main()