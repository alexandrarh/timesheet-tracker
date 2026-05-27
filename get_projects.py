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

    client_data = pd.DataFrame(columns=['Id', 'ClientId', 'ClientName'])

    for client in clients_response:
        client_row = pd.DataFrame({
            'Id': [client['Id']],
            'ClientId': [client['ClientId']],
            'ClientName': [client['ClientName']]
        })
        client_data = pd.concat([client_data, client_row], ignore_index=True)
        # print(f"Client ID: {client['Id']} - {client['ClientId']}, Name: {client['ClientName']}")

    # Get all projects
    projects_response = api.get_project_details()
    if isinstance(projects_response, str):
        print(projects_response)
        return

    project_data = pd.DataFrame(columns=['Id','ProjectId', 'ProjectName', 'ClientId'])

    for project in projects_response:
        project_row = pd.DataFrame({
            'Id': [project['Id']],
            'ProjectId': [project['ProjectId']],
            'ProjectName': [project['ProjectName']],
            'ClientId': [project['ClientId']]
        })
        project_data = pd.concat([project_data, project_row], ignore_index=True)
        # print(f"Project ID: {project['Id']}, Name: {project['ProjectId']} - {project['ProjectName']}. Belongs to Client ID: {project['ClientId']}")

    # Saving data to Excel file
    with pd.ExcelWriter('client_project_data.xlsx') as writer:
        client_data.to_excel(writer, sheet_name='Clients', index=False)
        project_data.to_excel(writer, sheet_name='Projects', index=False)

if __name__ == "__main__":
    main()