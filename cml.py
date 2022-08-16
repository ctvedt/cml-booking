import requests
from time import sleep
import uuid
from decouple import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Get environment variables
base_url = config('CML_API_BASE_URL')
username = config('CML_USERNAME')
password = config('CML_PASSWORD')
sendgrid_api_key = config('SENDGRID_API_KEY')
sendgrid_from_email = config('SENDGRID_FROM_EMAIL')
download_base_url = config('DOWNLOAD_BASE_URL')

# email for testing
email = config('DEBUG_EMAIL')

def GetToken(username, password):
    api_url = "authenticate"
    payload = { "username": username, "password": password }
    r = requests.post(base_url+api_url, json=payload, verify=False)
    print("GetToken: " + str(r.status_code))
    return r.json()

def GetListOfAllLabs(token):
    api_url = "labs?show_all=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(base_url+api_url, headers=head, verify=False)
    print("GetListOfAllLabs: " + str(r.status_code))
    return r.json()

def GetNodesInLab(token, labId):
    api_url = f"labs/{labId}/nodes?data=false"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(base_url+api_url, headers=head, verify=False)
    print("GetNodesInLab: " + str(r.status_code))
    return r.json()

def SaveNodeConfig(token, labId, node):
    api_url = f"labs/{labId}/nodes/{node}/extract_configuration"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(base_url+api_url, headers=head, verify=False)
    print("SaveNodeConfig: " + str(r.status_code))
    return r.json()

def DownloadLab(token, labId):
    api_url = f"labs/{labId}/download"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(base_url+api_url, headers=head, verify=False)
    print("DownloadLab: " + str(r.status_code))
    return r.text

def SaveLab(labId, labFile):
    labs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs/')
    if not os.path.isdir(labs_directory):
        os.mkdir(labs_directory)
    with open(f'{os.path.join(labs_directory, labId)}.yaml', 'w') as file:
        file.write(labFile)
    print(f'SaveLab: {labId}')

def StopLab(token, labId):
    api_url = f"labs/{labId}/stop"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(base_url+api_url, headers=head, verify=False)
    print("StopLab: " + str(r.status_code))
    return r.status_code

def DeleteLab(token, labId):
    api_url = f"labs/{labId}"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(base_url+api_url, headers=head, verify=False)
    print("DeleteLab: " + str(r.status_code))
    return r.status_code

def GetAdminId(token):
    api_url = "users/admin/id"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(base_url+api_url, headers=head, verify=False)
    print("GetAdminId: " + str(r.status_code))
    return r.json()

def LogAllUsersOut(token):
    api_url = "logout?clear_all_sessions=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(base_url+api_url, headers=head, verify=False)
    print("LogAllUsersOut: " + str(r.status_code))
    return r.status_code

def UpdateUserPassword(token, userId, oldpw, newpw):
    api_url = f"users/{userId}/"
    head = {'Authorization': f'Bearer {token}'}
    payload = { "password": {
        "old_password": oldpw,
        "new_password": newpw
        }
    }
    r = requests.patch(base_url+api_url, headers=head, json=payload, verify=False)
    print("UpdateUserPassword: " + str(r.status_code))
    return r.status_code

def SaveTempPassword(password):
    with open(f'temp_password', 'w') as file:
        file.write(password)

def SendEmail(email, title, content):
    message = Mail(
        from_email=sendgrid_from_email,
        to_emails=email,
        subject=title,
        html_content=content)
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f'SendEmail: {response.status_code}')
    except Exception as e:
        #print(e.message)
        print(f'SendEmail: FAILED')

# Generate random password and save it to file
temp_password = uuid.uuid4().hex
SaveTempPassword(temp_password)

def CleanUp():
    # Authenticate and get all labs
    token = GetToken(username, temp_password)
    labs = GetListOfAllLabs(token)
    # Loop through all labs, save config, stop and delete labs
    userlabs = []
    for lab in labs:
        nodes = GetNodesInLab(token, lab)
        for node in nodes:
            SaveNodeConfig(token, lab,node)
        userlabs.append(lab)
        SaveLab(lab, DownloadLab(token, lab))
        StopLab(token, lab)
        DeleteLab(token, lab)
    # Reset password
    UpdateUserPassword(token, GetAdminId(token), temp_password, password)
    # Re-authenticate and log out all users
    LogAllUsersOut(GetToken(username, password))
    # Email the user with download URL to their labs, if any
    if userlabs:
        lablinks = "Download links for your lab(s):<br>"
        for lab in userlabs:
            lablinks += f" - {download_base_url}" + lab +".yaml <br>"
        SendEmail(email, 'CML labs', f"Hi!<br><br>Your booked timeslot has unfortunatly come to an end, but don't worry!<br>All your labs are saved and can to be downloaded easily. <br><br>{lablinks}")

def CreateTempUser():
    # Create temporary password
    token = GetToken(username, password)
    UpdateUserPassword(token, GetAdminId(token), password, temp_password)

    # Send email to the user with the login information
    SendEmail(email, 'CML login info', f'Use these login credentials:<br><br>Username: {username}<br>Password: {temp_password}')

    print("...sleeping for 30s...")
    sleep(30)
    CleanUp()

CreateTempUser()
