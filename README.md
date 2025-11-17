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
- Python 3.12+
- TimeSolv firm **and** developer account
    - Will need `client_id`, `client_secret`, `redirect_uri`, and `auth_code`
- Microsoft Graph API account (with global administrator permissions)
    - Will need `client_id`, `client_secret`, and `tenant_id`
- GitHub repository (to run automation)

## Set up 
This program can be ran locally **and/or** with automation, please refer to each section based on your needs. For any aspects requiring production keys/secrets, refer to the [Configuration Guide](#configuration-guide) for obtaining proper keys/secrets needed for TimeSolv and Microsoft Graph API.

### Running on local environment (for testing purposes)
To run the program locally, follow the steps below.
1. Clone the repository onto local environment. 
    <p><img src="images/clone.png" alt="Cloning the repo" style="width:45%; height:auto;"></p>
2. Open the repository on IDE (preferrably Visual Studio Code) and open a New Terminal.
    <p><img src="images/terminal.png" alt="Opening a new terminal" style="width:40%; height:auto;"></p>
3. In the terminal, create the virtual environment using the following command(s).
    #### If using bash/zsh
    ```shell
    python3 -m venv .venv
    ```
    #### If using Windows
    ```bat
    c:\>c:\Python35\python -m venv .venv
    ```
4. Activate the virtual environment with the following command(s).
    #### If using bash/zsh
    ```shell
    source .venv/bin/activate
    ```
    #### If using Windows
    ```bat
    C:\> .venv\Scripts\activate.bat
    ```
5. Install the proper packages from `requirements.txt` in the terminal with the following command.
```shell
pip install -r requirements.txt
```
6. Configure your `.env` file (must be created in repository on local). For an example on formatting, refer to [.env.example](/.env.example) in this repository. For configuration, refer to [Configuration Guide](#configuration-guide) below on `.env` setup and obtaining proper keys for TimeSolv and Microsoft Graph API.

7. Use the following command into the terminal to run the local/test program, `local_test.py`
```shell
python local_test.py
```
**NOTE**: When running the program, a `status_test.log` should be created, and it will contain any logs/output generated from the local test. There should also be two emails sent to the specified email(s) in the `.env` file (`SENDER_EMAIL` and `ADMIN_EMAILS` variables).

### Running on production environment
To run this program on a production environment, follow the steps below.
1. Fork the `timesheet-tracker` repo onto the preferred account.
    <figure><img src="images/fork_1.png" alt="Navigating creating a new fork" style="width:45%; height:auto;"><figcaption>Navigating creating a new fork</figcaption></figure>
    <figure><img src="images/fork_2.jpg" alt="Creating a new fork" style="width:45%; height:auto;"><figcaption>Creating a new fork</figcaption></figure>

## Configuration Guide