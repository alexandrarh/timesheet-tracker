import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
from typing import Dict
import ast

load_dotenv()
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_NAME: str = os.getenv("SUPABASE_TABLE_NAME")

class SupabaseAPI:
    """Handles Supabase client creation and connection."""
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_client(self) -> Client:
        """Returns the Supabase client instance."""
        return self.supabase
    
    def fetch_existing_submission_data(self, user_id: int) -> tuple[list, int]:
        """
        Fetches all user data from the Supabase submissions table.

        Args:
        - user_id (int): The UserId to fetch data for.

        Returns:
        - List of records from the Supabase submissions table.
        """
        response = self.supabase.table(SUPABASE_TABLE_NAME).select("NoSubmissionDates, NoSubmissionCount").eq("UserId", user_id).execute()
        no_submission_dates = response.data[0]['NoSubmissionDates'] if response.data else []
        no_submission_count = response.data[0]['NoSubmissionCount'] if response.data else 0

        return no_submission_dates, no_submission_count

    def remove_dates(self, data: pd.DataFrame):
        """
        Removes specified dates from the Supabase submissions table.

        Args:
        - data (pd.DataFrame): DataFrame containing the data to be updated in the Supabase submissions table.
        """
        records = []

        for _, row in data.iterrows():
            # Handle NoSubmissionDates
            dates = row['NoSubmissionDates']
            if isinstance(dates, str):
                dates = ast.literal_eval(dates) if dates else None
            elif not dates or (isinstance(dates, float) and pd.isna(dates)):
                dates = None
            
            existing_dates, existing_count = self.fetch_existing_submission_data(int(row['UserId']))
            if existing_dates:
                # Remove specified dates from existing dates
                updated_dates = [date for date in existing_dates if date not in dates] if dates else existing_dates
                dates = updated_dates
                no_submission_count = len(updated_dates)
            else:
                no_submission_count = existing_count
                
            records.append({
                "UserId": int(row['UserId'])
                "NoSubmissionDates": dates if dates else [],  
                "NoSubmissionCount": no_submission_count,
                "lastUpdateDate": row['lastUpdateDate'] if pd.notna(row['lastUpdateDate']) else None,
                "Comments": row['Comments'] if pd.notna(row['Comments']) else None
            })

        response = self.supabase.table(SUPABASE_TABLE_NAME).upsert(records, on_conflict="UserId").execute()
        return response
    
    def update_dates(self, data: pd.DataFrame):
        """
        Updates the Supabase submissions table with new data.

        Args:
        - data (pd.DataFrame): DataFrame containing the data to be added or updated in the Supabase submissions table.
        """
        records = []

        for _, row in data.iterrows():
            # Handle NoSubmissionDates
            dates = row['NoSubmissionDates']
            if isinstance(dates, str):
                dates = ast.literal_eval(dates) if dates else None
            elif not dates or (isinstance(dates, float) and pd.isna(dates)):
                dates = None

            existing_dates, existing_count = self.fetch_existing_submission_data(int(row['UserId']))
            if existing_dates:
                # Merge existing dates with new dates, avoiding duplicates
                merged_dates = list(set(existing_dates) | set(dates)) if dates else existing_dates
                dates = merged_dates
                no_submission_count = len(merged_dates)
            else:
                no_submission_count = len(dates)
                
            records.append({
                "UserId": int(row['UserId']),
                "Email": row['Email'],
                "Name": row['Name'],
                "NoSubmissionDates": dates if dates else [],  
                "NoSubmissionCount": no_submission_count,
                "lastEmailSentDate": row['lastEmailSentDate'] if pd.notna(row['lastEmailSentDate']) else None,
                "lastUpdateDate": row['lastUpdateDate'] if pd.notna(row['lastUpdateDate']) else None,
                "Comments": row['Comments'] if pd.notna(row['Comments']) else None
            })

        response = self.supabase.table(SUPABASE_TABLE_NAME).upsert(records, on_conflict="UserId").execute()
        return response