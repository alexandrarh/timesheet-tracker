import requests
import msal
import json
import os
from dotenv import load_dotenv
import base64
import pandas as pd
from typing import List, Dict, Tuple
import ast
 
load_dotenv()
CLIENT_ID = os.getenv('MICROSOFT_CLIENT_ID')
CLIENT_SECRET = os.getenv('MICROSOFT_CLIENT_SECRET')
TENANT_ID = os.getenv('MICROSOFT_TENANT_ID')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')

class EmailDraft:
    def get_access_token(self) -> tuple[bool, str]:
        """
        Authenticate with Microsoft Graph API to get token.

        Returns:
        - A tuple containing a boolean indicating success, and the access token or error message.
        """
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

    def statistics_generator(self, users: pd.DataFrame) -> tuple[pd.DataFrame, int, pd.Series, pd.DataFrame]:
        """
        Generate statistics on users with missing time sheet submissions.
        
        Args:
        - users: DataFrame containing user data with 'NoSubmissionDates' column.

        Returns:
        - top_5_no_subs: DataFrame with top 5 users by missing submission count
        - percentage_missing: Percentage of users with missing submissions
        - most_frequent_day: Series of most frequently missed dates
        - user_error_desc: DataFrame of users with errors
        - file_path: Path to the generated bar graph image
        """
        # Top 5 users with most missing submissions
        users['NoSubmissionCount'] = pd.to_numeric(users['NoSubmissionCount'], errors='coerce')
        top_5 = users.nlargest(5, 'NoSubmissionCount')
        top_5_no_subs = top_5[['Name', 'NoSubmissionDates', 'NoSubmissionCount']]

        # Percentage of users with missing submissions
        total_users = len(users)
        users_with_missing_submissions = users[users['NoSubmissionCount'] > 0]
        total_missing = len(users_with_missing_submissions)
        percentage_missing = round((total_missing / total_users * 100), 2) if total_users > 0 else 0

        # Most frequently missed dates (Series)
        all_days = users['NoSubmissionDates'].explode()
        days_count = all_days.value_counts()
        
        # Handle case where there are no missing dates
        if len(days_count) > 0:
            highest_count = days_count.max()
            most_frequent_day = days_count[days_count == highest_count]
        else:
            most_frequent_day = pd.Series(dtype=int)  # Empty series

        # Users with errors
        users_with_errors = users[users['Comments'] != ""]
        user_error_desc = users_with_errors[['Name', 'NoSubmissionDates', 'Comments']]

        return top_5_no_subs, percentage_missing, most_frequent_day, user_error_desc


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

        Returns:
        - A tuple containing a boolean indicating success, and a message string.
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

    def summary_email(self, token, to_email, users, start_date, end_date) -> tuple[bool, str]:
        """
        Send a summary email listing all users with missing time sheet submissions.
        
        Args:
        - token: The access token for Microsoft Graph API.
        - to_email: The recipient's email address, admins.
        - users: Dataframe containing user data with 'NoSubmissionDates' column.
        - start_date: Start date of the work week.
        - end_date: End date of the work week.

        Returns:
        - A tuple containing a boolean indicating success, and a message string.
        """

        # Summary/statistics report of all users with missing submissions
        top_5_no_subs, percentage_missing, most_frequent_day, user_error_desc = self.statistics_generator(users)

        # Format most frequently missed dates as comma-separated list
        if len(most_frequent_day) > 0:
            frequent_dates_str = ', '.join(most_frequent_day.index.astype(str))
        else:
            frequent_dates_str = "None"

        # Format top 5 users
        top_5_html = ""
        if len(top_5_no_subs) > 0:
            for index, row in top_5_no_subs.iterrows():
                top_5_html += f"                <li><strong>{row['Name']}</strong>: {row['NoSubmissionDates']}</li>\n"
        else:
            top_5_html = "                <li>None</li>"

        # Format users with errors
        if len(user_error_desc) > 0:
            errors_html = ""
            for _, row in user_error_desc.iterrows():
                name = row['Name']
                comments = row['Comments']
                errors_html += f"                <li><strong>{name}</strong>: {comments}</li>\n"
        else:
            errors_html = "None"
        
        body = f"""<html>
        <body style="font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #333;">
            <p>Dear Admins,</p>
            <p>Here is a summary for the recent time sheet submissions for the work week <strong>{start_date} to {end_date}</strong>:</p>
            
            <ul style="line-height: 1.5;">
                <li><strong>Top 5 Users with Most Missing Submissions:</strong>
                    <ul>
        {top_5_html}
                    </ul>
                </li>
                <li><strong>Percentage of Users with Missing Submissions:</strong> {percentage_missing}%</li>
                <li><strong>Most Frequently Missed Date(s):</strong> {frequent_dates_str}</li>
                <li><strong>Users with Errors:</strong>
                    {'<ul>' if len(user_error_desc) > 0 else ''}
        {errors_html if len(user_error_desc) > 0 else '            None'}
                    {'</ul>' if len(user_error_desc) > 0 else ''}
                </li>
            </ul>
            
            <p>Please refer to the attached file for the full data from the work week.</p>
            
            <p>Best regards,<br>Alexandra Hernandez</p>
        </body>
        </html>"""

        subject = "Summary of Users with Missing Time Sheet Submissions for Work Week " + start_date + " to " + end_date

        # Saving the summary report as an attachment (CSV file for simplicity)
        filename = 'missing_time_sheets_summary.csv'
        users.to_csv(filename, index=False)
        with open(filename, 'rb') as f:
            file_content = f.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')

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
                    'contentType': 'HTML', 
                    'content': body
                },
                'toRecipients': to_recipients,
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentType": "text/csv",
                        "contentBytes": encoded_content
                    }
                ]
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
        message_str = f"Email sent successfully."
        os.remove('missing_time_sheets_summary.csv')    # Clean up the attachment file
        return status, message_str