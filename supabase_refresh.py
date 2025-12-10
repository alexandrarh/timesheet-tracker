from timesolv_api import TimeSolvAPI, TimeSolveAuth
import logging
import logging.handlers
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
from typing import List, Dict
import time
import os
import pandas as pd
from dotenv import load_dotenv
import ast
from supabase_api import SupabaseAPI

# This file will be dedicated to refreshing data in Supabase from TimeSolv
# Will check if any users have not submitted timesheets for the past week -> if so, remove dates from Supabase, and update count
# Will also run as a separate automation independent of the original timesheet_tracker.py script -> will run weekly on Saturday or Sunday (start of week or end of week)

# Eastern time, regardless of UTC
CURRENT_DATE = datetime.now(ZoneInfo('America/New_York')).date()

def get_work_week_dates():
    """
    Get the start (Monday) and end (Friday) dates of the current work week.

    Returns:
    - List of dates as strings in 'YYYY-MM-DD' format.
    """
    # Use Eastern time to get the correct "today" regardless of UTC time
    monday = CURRENT_DATE - timedelta(days=CURRENT_DATE.weekday())
    
    # Generate all 5 work days
    work_week = [monday + timedelta(days=i) for i in range(5)]
    
    return [day.strftime('%Y-%m-%d') for day in work_week]

def get_previous_work_week_dates():
    """
    Get the start (Monday) and end (Friday) dates of the previous work week.

    Returns:
    - List of dates as strings in 'YYYY-MM-DD' format.
    """
    today = CURRENT_DATE
    current_monday = today - timedelta(days=today.weekday())
    
    # Get Monday of previous week (7 days before current Monday)
    previous_monday = current_monday - timedelta(days=7)
    
    # Generate all 5 work days
    previous_work_week = [previous_monday + timedelta(days=i) for i in range(5)]
    
    return [day.strftime('%Y-%m-%d') for day in previous_work_week]

