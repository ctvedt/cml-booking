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
import logging
logger = logging.getLogger(__name__)


def GetToken(username, password):
    """
    Authenticate with username and password and get API token

    Status codes:
      Success: 200
      Failure: 403
    """
    api_url = "authenticate"
    payload = { "username": username, "password": password }
    r = requests.post(settings.CML_API_BASE_URL+api_url, json=payload, verify=False)
    logger.info(f"GetToken: {r.status_code}")
    return r.json(), r.status_code

def GetListOfAllLabs(token):
    """
    Return a list of all labs

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = "labs?show_all=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"GetListOfAllLabs: {r.status_code}")
    return r.json(), r.status_code

def GetNodesInLab(token, labId):
    """
    Return a list of all nodes in a given lab

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = f"labs/{labId}/nodes?data=false"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"GetNodesInLab: {r.status_code}")
    return r.json(), r.status_code

def SaveNodeConfig(token, labId, node):
    """
    Extract and save node config for a given node in a given lab

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = f"labs/{labId}/nodes/{node}/extract_configuration"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"SaveNodeConfig: {r.status_code}")
    return r.json(), r.status_code

def DownloadLab(token, labId):
    """
    Download a given lab

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = f"labs/{labId}/download"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"DownloadLab: {r.status_code}")
    return r.text, r.status_code

def SaveLab(labId, labFile):
    """
    Save a given lab to file
    """
    labs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labs/')
    if not os.path.isdir(labs_directory):
        os.mkdir(labs_directory)
    with open(f'{os.path.join(labs_directory, labId)}.yaml', 'w') as file:
        file.write(labFile)
    logger.info(f"SaveLab: {labId}")

def StopLab(token, labId):
    """
    Stop a given lab

    Status codes:
      Success: 204
      Failure: any other values
    """
    api_url = f"labs/{labId}/stop"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"StopLab: {r.status_code}")
    return r.status_code

def WipeLab(token, labId):
    """
    Wipe a given lab

    Status codes:
      Success: 204
      Failure: any other values
    """
    api_url = f"labs/{labId}/wipe"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.put(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"WipeLab: {r.status_code}")
    return r.status_code

def DeleteLab(token, labId):
    """
    Delete a given lab

    Status codes:
      Success: 204
      Failure: any other values
    """
    api_url = f"labs/{labId}"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"DeleteLab: {r.status_code}")
    return r.status_code

def GetAdminId(token):
    """
    Return the ID of the admin account

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = "users/admin/id"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.get(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"GetAdminId: {r.status_code}")
    return r.json(), r.status_code

def LogAllUsersOut(token):
    """
    Clears sessions and log out everyone

    Status codes:
      Success: 200
      Failure: 401 / any other values
    """
    api_url = "logout?clear_all_sessions=true"
    head = {'Authorization': f'Bearer {token}'}
    r = requests.delete(settings.CML_API_BASE_URL+api_url, headers=head, verify=False)
    logger.info(f"LogAllUsersOut: {r.status_code}")
    return r.status_code

def UpdateUserPassword(token, userId, oldpw, newpw):
    """
    Updates the password for a given user ID

    Status codes:
      Success: 200
      Failure: any other values
    """
    api_url = f"users/{userId}/"
    head = {'Authorization': f'Bearer {token}'}
    payload = { 
        "password": 
        {
            "old_password": oldpw,
            "new_password": newpw
        }
    }
    r = requests.patch(settings.CML_API_BASE_URL+api_url, headers=head, json=payload, verify=False)
    logger.info(f"UpdateUserPassword: {r.status_code}")
    return r.status_code

def SendEmail(email, title, content, attachments=None):
    """
    Sends an email with input title and content. Attachment is optional.

    Status codes:
      Success: 202
      Failure: any other values
    """
    # Create message
    message = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=email,
        subject=title,
        html_content=content)

    # Add BCC if configured
    if (settings.SENDGRID_BCC_EMAIL):
        message.add_bcc(settings.SENDGRID_BCC_EMAIL)

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
        logger.info(f"SendEmail: Sending email to {email} with subject {title}.")
        logger.info(f"SendEmail: SendGridAPI status code: {response.status_code}")
        return response.status_code
    except Exception as e:
        logger.error(f"SendEmail: Failed to send email")
        logger.info(f"SendEmail: SendGridAPI status code: {response.status_code}")
        logger.debug(f"SendEmail: Exception: {e}")
        return response.status_code

def CleanUp(email, temp_password):
    """
    Clean up labs when timeslot has reached the end
    """
    # Authenticate and get all labs
    logger.info(f"CleanUp: Starting cleanup")
    token, statuscode = GetToken(settings.CML_USERNAME, temp_password)
    labs, statuscode = GetListOfAllLabs(token)
    
    # Loop through all labs, save config, stop and delete labs
    userlabs = []
    for lab in labs:
        nodes, statuscode = GetNodesInLab(token, lab)
        for node in nodes:
            # TODO: Extract of config only works if node is running, so should check that first
            savenode, statuscode = SaveNodeConfig(token, lab,node)
        userlabs.append(lab)
        savelab, statuscode = SaveLab(lab, DownloadLab(token, lab))
        statuscode = StopLab(token, lab)
        statucode = WipeLab(token, lab)
        statuscode = DeleteLab(token, lab)
    
    # Reset password
    adminid, statuscode = GetAdminId(token)
    statuscode = UpdateUserPassword(token, adminid, temp_password, settings.CML_PASSWORD)
    
    # Re-authenticate and log out all users
    token, statuscode = GetToken(settings.CML_USERNAME, settings.CML_PASSWORD)
    statuscode = LogAllUsersOut(token)
    
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
    body = render_to_string('booking/email_teardown.html', context)
    statuscode = SendEmail(email, 'Community Network - CML reservasjon er utløpt', body, attachments)

def CreateTempUser(email, temp_password):
    """
    Create an temporary password and send the credentials via email
    """
    logger.info(f"CreateTempUser: Creating user for {email}")
    # Get token and update username
    token, statuscode = GetToken(settings.CML_USERNAME, settings.CML_PASSWORD)
    adminid, statuscode = GetAdminId(token)
    statuscode = UpdateUserPassword(token, adminid, settings.CML_PASSWORD, temp_password)
    
    # Send email to the user with the login information using template
    context = {
        'username': settings.CML_USERNAME,
        'password': temp_password,
        'cml_url': settings.CML_URL,
        'booking_url': settings.BOOKING_URL,
    }
    body = render_to_string('booking/email_setup.html', context)
    statuscode = SendEmail(email, 'Community Network - CML påloggingsinformasjon', body)