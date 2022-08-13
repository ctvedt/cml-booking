import requests
from time import sleep
import uuid
from decouple import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get environment variables
base_url = config('CML_API_BASE_URL')
username = config('CML_USERNAME')
password = config('CML_PASSWORD')

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
    with open(f'lab_{labId}.yaml', 'w') as file:
        file.write(f'./labs/{labFile}')

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

def SendUsernameAndPassword(email, password):
    pass

def SendConfigs(email):
    pass

# Generate random password and save it to file
temp_password = uuid.uuid4().hex
SaveTempPassword(temp_password)

def CleanUp():
    # Authenticate and get all labs
    token = GetToken(username, temp_password)
    labs = GetListOfAllLabs(token)
    # Loop through all labs, save config, stop and delete labs
    for lab in labs:
        nodes = GetNodesInLab(token, lab)
        for node in nodes:
            SaveNodeConfig(token, lab,node)
        SaveLab(lab, DownloadLab(token, lab))
        StopLab(token, lab)
        DeleteLab(token, lab)
    # Reset password
    UpdateUserPassword(token, GetAdminId(token), temp_password, password)
    # Re-authenticate and log out all users
    LogAllUsersOut(GetToken(username, password))

def CreateTempUser():
    token = GetToken(username, password)
    UpdateUserPassword(token, GetAdminId(token), password, temp_password)
    print("...sleeping for 30s...")
    sleep(30)
    CleanUp()

CreateTempUser()
