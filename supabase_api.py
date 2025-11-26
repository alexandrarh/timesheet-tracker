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
                
            records.append({
                "UserId": int(row['UserId']),
                "Email": row['Email'],
                "Name": row['Name'],
                "NoSubmissionDates": dates if dates else [],  
                "NoSubmissionCount": int(row['NoSubmissionCount']) if pd.notna(row['NoSubmissionCount']) else 0,
                "lastEmailSentDate": row['lastEmailSentDate'] if pd.notna(row['lastEmailSentDate']) else None,
                "lastUpdateDate": row['lastUpdateDate'] if pd.notna(row['lastUpdateDate']) else None,
                "Comments": row['Comments'] if pd.notna(row['Comments']) else None
            })

        response = self.supabase.table(SUPABASE_TABLE_NAME).upsert(records, on_conflict="UserId").execute()
        return response