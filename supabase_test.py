import os
from urllib import response
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Example query to test the connection -> fetching data
    fetch_response = (
        supabase.table("no_submission_dates_test")
        .select("*")
        .limit(5)
        .execute()
    )
    for record in fetch_response.data:
        print(record)

    # Inserting new data
    insert_response = (
        supabase.table("no_submission_dates_test")
        .insert(
                {
                    "UserId": 11111, 
                    "Email": "insert1@company.url", 
                    "Name": "J F", 
                    "NoSubmissionDates": ["2025-06-15"], 
                    "NoSubmissionCount": 1, 
                    "lastEmailSentDate": "2025-11-13 10:45:18+00", 
                    "lastUpdateDate": "2025-11-13 10:45:18+00", 
                    "Comments": None
                }
            )
        .execute()
    )

    # Inserting multiple rows
    insert_multiple_response = (
        supabase.table("no_submission_dates_test")
        .insert(
            [
                {
                    "UserId": 22222, 
                    "Email": "insert2@company.url",
                    "Name": "K L", 
                    "NoSubmissionDates": ["2025-07-20"], 
                    "NoSubmissionCount": 1, 
                    "lastEmailSentDate": "2025-11-14 11:30:00+00", 
                    "lastUpdateDate": "2025-11-14 11:30:00+00", 
                    "Comments": None
                },
                {
                    "UserId": 33333, 
                    "Email": "insert3@company.url", 
                    "Name": "M N", 
                    "NoSubmissionDates": ["2025-08-10", "2025-07-20"], 
                    "NoSubmissionCount": 2, 
                    "lastEmailSentDate": "2025-11-15 12:00:00+00", 
                    "lastUpdateDate": "2025-11-15 12:00:00+00", 
                    "Comments": None
                }
            ]
        )
        .execute()
    )

    # Updating existing data
    update_response = (
        supabase.table("no_submission_dates_test")
        .update(
            {
                "NoSubmissionDates": [], 
                "NoSubmissionCount": 0
            }
        )
        .eq("UserId", 11111)
        .execute()
    )


except Exception as e:
    print(f"Error with Supabase client: {e}")