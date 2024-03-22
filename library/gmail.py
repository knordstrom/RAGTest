import os
import pickle

from library import models

# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
import os

class Gmail:
    # Request all access (permission to read/send/receive emails, manage the inbox, and more)
    SCOPES = ['https://mail.google.com/']
    #our_email = 'your_gmail@gmail.com'

    @property
    def service(self):
        return self.__authenticate()

    def __init__(self, email, creds):
        self.email = email
        self.creds = creds

    def __authenticate(self):
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

    def get_emails(self) -> list:
        # call the Gmail API
        results = self.service.users().messages().list(userId='me').execute()
        messages = results.get('messages', [])
        print("Got messages: " + str(messages))
        return messages
    
    def get_email(self, user_id: str='me', msg_id: str='') -> str:
        print("Getting email with id " + msg_id + " for user " + user_id)
        data = self.service.users().messages().get(userId=user_id, id=msg_id).execute()['payload']
        if data.get("parts"):
            vals = data['parts']
        else:
            vals = []
        for v in vals:
            if v['mimeType'] == 'text/plain':
                return urlsafe_b64decode(str(v['body']['data'])).decode()
        
        message = map(lambda m: m.get('body'), vals)
        # print("Got email: " + str(message))
        return str(message)
    

    def read_message(self, user_id: str='me', message: str=''):
        """
        This function takes Gmail API `service` and the given `message_id` and does the following:
            - Downloads the content of the email
            - Prints email basic information (To, From, Subject & Date) and plain/text parts
            - Creates a folder for each email based on the subject
            - Downloads text/html content (if available) and saves it under the folder created as index.html
            - Downloads any file that is attached to the email and saves it in the folder created
        """
        msg = self.service.users().messages().get(userId=user_id, id=message, format='full').execute()
        # parts can be the message body, or attachments
        payload = msg['payload']['parts']
        return payload
    

    def close(self):
        self.service.close()
