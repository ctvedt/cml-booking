import requests
from time import sleep
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import base64
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId
from django.conf import settings


def GetToken(username, password):
    api_url = "authenticate"
    payload = { "username": username, "password": password }
    r = requests.post(settings.CML_API_BASE_URL+api_url, json=payload, verify=False)
    print("GetToken: " + str(r.status_code))
    return r.json()

def GetListOfAllLabs(token):
    api_url = "labs?show_all=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("GetListOfAllLabs: " + str(r.status_code))
    return r.json()

def GetNodesInLab(token, labId):
    api_url = f"labs/{labId}/nodes?data=false"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("GetNodesInLab: " + str(r.status_code))
    return r.json()

def SaveNodeConfig(token, labId, node):
    api_url = f"labs/{labId}/nodes/{node}/extract_configuration"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("SaveNodeConfig: " + str(r.status_code))
    return r.json()

def DownloadLab(token, labId):
    api_url = f"labs/{labId}/download"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
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
    r = requests.put(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("StopLab: " + str(r.status_code))
    return r.status_code

def DeleteLab(token, labId):
    api_url = f"labs/{labId}"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("DeleteLab: " + str(r.status_code))
    return r.status_code

def GetAdminId(token):
    api_url = "users/admin/id"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    print("GetAdminId: " + str(r.status_code))
    return r.json()

def LogAllUsersOut(token):
    api_url = "logout?clear_all_sessions=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
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
    r = requests.patch(settings.CML_API_BASE_URL+api_url, headers=head, json=payload, verify=False)
    print("UpdateUserPassword: " + str(r.status_code))
    return r.status_code

def SendEmail(email, title, content, attachments=None):
    # Create message
    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=email,
        subject=title,
        html_content=content)

    # If there are any attachment to be sendt
    if attachments:
        for file in attachments:
            # Remove path from filename
            filename = file.split('/')[-1]

            # Verify that the file exists. If not, ignore
            if os.path.exists(file):
                # Read file
                with open(file, 'rb') as f:
                    data = f.read()
                    f.close()
                
                # Create attachment
                file = Attachment()
                file.file_content = FileContent(base64.b64encode(data).decode())
                file.file_type = FileType('text/plain')
                file.file_name = FileName(filename)
                file.disposition = Disposition('attachment')
                file.content_id = ContentId(filename)

                # Attach to message
                message.attachment = file

    try:
        sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sendgrid_client.send(message)
        print(f'SendEmail: {response.status_code}')
    except Exception as e:
        print(f'SendEmail: FAILED')

def CleanUp(email, temp_password):
    # Authenticate and get all labs
    token = GetToken(settings.CML_USERNAME, temp_password)
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
    UpdateUserPassword(token, GetAdminId(token), temp_password, settings.CML_PASSWORD)
    
    # Re-authenticate and log out all users
    LogAllUsersOut(GetToken(settings.CML_USERNAME, settings.CML_PASSWORD))
    
    # Loop through the labs and create list of attachments, if any
    attachments = []
    if userlabs:
        for lab in userlabs:
            labs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs/')
            attachments.append(f'{labs_directory}{lab}.yaml')

    # Send the user an email (with attachments, if any) using template
    context = {
        'cml_url': settings.CML_URL,
        'booking_url': settings.BOOKING_URL,
    }
    body = render_to_string('booking/email_teardown.html' context)
    SendEmail(email, 'Community Network - CML reservasjon er utløpt', body, attachments)

def CreateTempUser(email, temp_password):
    # Get token and update username
    token = GetToken(settings.CML_USERNAME, settings.CML_PASSWORD)
    UpdateUserPassword(token, GetAdminId(token), settings.CML_PASSWORD, temp_password)
    
    # Send email to the user with the login information using template
    context = {
        'username': settings.CML_USERNAME,
        'password': temp_password,
        'cml_url': settings.CML_URL,
        'booking_url': settings.BOOKING_URL,
    }
    body = render_to_string('booking/email_setup.html', context)
    SendEmail(email, 'Community Network - CML påloggingsinformasjon', body)