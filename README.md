# TimeSolv Timesheet Tracker
Built with Python and GitHub Actions, this aims to validate TimeSolv firm employees' timesheets, and pick up on any users that don't submit timesheets for certain dates during the work week. This bot runs weekly to ensure everyone is evaluated accordingly.

## How it works
The checker runs automatically on a schedule and validates timesheet completeness:

<p align="center">
  <img src="images/program_flow_diagram_cropped.png" alt="Alt Text" style="width:85%; height:auto;">
</p>

The workflow fetches user information and timesheet data from TimeSolv and user information, identifies missing entries, notifies affected users via email with calls to Microsoft Graph API, and sends a summary report to administrators.

## Prerequisites
In order to run the TimeSolv Timesheet Tracker, these components are required:
- TimeSolv firm **and** developer account
    - Will need `client_id`, `client_secret`, `redirect_uri`, and `auth_code`
- Microsoft Graph API account (with global administrator permissions)
    - Will need `client_id`, `client_secret`, and `tenant_id`
- GitHub repository (to run automation)

## Set up 
This program can be ran locally **and/or** with automation, please refer to each section based on your needs. 

### Running on local environment (for testing purposes)
1. Clone the repository onto local environment. <br>
     <br><img src="images/clone.png" alt="Alt Text" style="width:30%; height:auto;"></br>
2. Something

### Running on production environment