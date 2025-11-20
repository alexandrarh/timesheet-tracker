import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase.table("no_submission_dates_test")
        .select("*")
        .limit(5)
        .execute()
    )
    
    for record in response.data:
        print(record)

    # print("Supabase client created successfully.")
except Exception as e:
    print(f"Error creating Supabase client: {e}")