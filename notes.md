# Notes/outline for project

### Necessary imports + aspects
```python
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set
import logging
import logging.handlers
import os

# [access token] -> must be kept in secret vars
```

## Components
### API class file
- Should contain API callbacks and access token usage
- Uses TimeSolv API calls: `/firmUserSearch`, `/timeCardSearch`
- Retrieves + returns who hasn't submitted time cards for given time period

### Main file
- Should be ran by `.github/workflows/actions.yaml` or whatever the `.yaml` file will be called (automation aspect)
- Implement access token here (call to SECRETS in repo)
    - See `experience/work-files/insite_work/insite-files/cron_job_test` for reference 
- Log errors and codes returned from API class file
- Incorporate current day (checked, see if can do auto)
- Gets users who didn't log in time, sends them email
    - Let's get count of users time card (how many did they submit) -> number should be 5 arbitrary?
    - Not sure what other form of communication to remind that will be just Internet based

### Workflow file
- Contains the components that will help GitHub Actions run (automated aspect)
    - Refer to `experience/work-files/insite_work/insite-files/cron_job_test/../actions.yaml` file
- Should run daily (1x a day, EOD)
