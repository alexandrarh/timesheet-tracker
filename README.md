# TimeSolv timesheet tracker
TimeSolv timesheet tracker for firm

## How it works
The checker runs automatically on a schedule and validates timesheet completeness:

<p align="center">
  <img src="images/program_flow_diagram_cropped.png" alt="Alt Text" style="width:50%; height:auto;">
</p>

The workflow fetches timesheet data from TimeSolv and user information from Microsoft Graph, identifies missing entries, notifies affected users, and sends a summary report to administrators.