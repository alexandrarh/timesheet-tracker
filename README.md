# TimeSolv timesheet tracker
TimeSolv timesheet tracker for firm

## How it works
The checker runs automatically on a schedule and validates timesheet completeness:
```mermaid
---
title: Timesheet Tracker Diagram
---
%%{init: {'theme':'light'}}%%
flowchart LR
    A@{shape: notch-pent, label: "GitHub Actions"} --> B@{shape: rect, label: "Python Script"}
    B --> C@{shape: subproc, label: "TimeSolv API"}
    B --> D@{shape: subproc, label: "Microsoft Graph API"}
    C --> E@{shape: rect, label: "Validate missing dates"} --> F
    D --> F@{shape: rounded, label: "Notify users with missing dates"}
    F --> G@{shape: rect, label: "Summarize missing dates"}
    G --> H@{shape: stadium, label: "Send summary to admins"}
    
    style A fill:#2088ff,stroke:#0366d6,color:#fff,stroke-width:2px
    style B fill:#28a745,stroke:#22863a,color:#fff,stroke-width:2px
    style C fill:#ffa500,stroke:#ff8c00,color:#fff,stroke-width:2px
    style D fill:#ffa500,stroke:#ff8c00,color:#fff,stroke-width:2px
    style E fill:#6f42c1,stroke:#5a32a3,color:#fff,stroke-width:2px
    style F fill:#dc3545,stroke:#bd2130,color:#fff,stroke-width:2px
    style G fill:#6f42c1,stroke:#5a32a3,color:#fff,stroke-width:2px
    style H fill:#17a2b8,stroke:#138496,color:#fff,stroke-width:2px
```
The workflow fetches timesheet data from TimeSolv and user information from Microsoft Graph, identifies missing entries, notifies affected users, and sends a summary report to administrators.