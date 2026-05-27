from timesolv_api import TimeSolvAPI, TimeSolveAuth
import time
import os
import pandas as pd

def main():
    # Authenticate and get access token
    auth = TimeSolveAuth()
    success, result = auth.get_access_token()
    if not success:
        print(result)
        return

    access_token = result
    api = TimeSolvAPI(access_token)

    # Get clients
    clients_response = api.get_client_details()
    if isinstance(clients_response, str):
        print(clients_response)
        return

    for client in clients_response:
        print(f"Client ID: {client['Id']} - {client['ClientId']}, Name: {client['ClientName']}")

    # Get all projects
    projects_response = api.get_project_details()
    if isinstance(projects_response, str):
        print(projects_response)
        return

    # project_data = pd.DataFrame(columns=['Id','ProjectId', 'ProjectName', 'ClientId'])

    print("Projects retrieved successfully:")
    for project in projects_response:
        print(f"Project ID: {project['Id']}, Name: {project['ProjectId']} - {project['ProjectName']}. Belongs to Client ID: {project['ClientId']}")

if __name__ == "__main__":
    main()