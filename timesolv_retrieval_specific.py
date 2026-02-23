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