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