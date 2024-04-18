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

# interface for the Gmail API wrapper
class GmailServiceProvider:

    def service(self):
        pass

    def list(self, userId='me', pageToken=None, maxResults = None):
        pass

    def get(self, id, userId='me', format='full'):
        pass

    def close(self):
        pass
    

# Dependency Injectable Gmail methods
class GmailLogic:
    def __init__(self, gmail: GmailServiceProvider):
        self.gmail = gmail

    def get_emails(self, count = None) -> list:
        pageToken = None
        messages_left = True
        messages = []

        while messages_left:
            results = self.gmail.list(userId='me', pageToken=pageToken, maxResults=count)
            pageToken = results.get('nextPageToken')
            new_messages = results.get('messages', [])
            count -= len(new_messages)
            messages += new_messages
            if not pageToken or (not count or count <= 0) or len(new_messages) == 0:               
                messages_left = False
        return messages
    
    def get_email(self, user_id: str='me', msg_id: str='') -> dict:
        print("Getting email with id " + msg_id + " for user " + user_id)
        data = self.gmail.get(userId=user_id, id=msg_id)
        return models.Message.extract_data(data)
    

    def read_message(self, user_id: str='me', message: str=''):
        """
        This function takes Gmail API `service` and the given `message_id` and does the following:
            - Downloads the content of the email
            - Prints email basic information (To, From, Subject & Date) and plain/text parts
            - Creates a folder for each email based on the subject
            - Downloads text/html content (if available) and saves it under the folder created as index.html
            - Downloads any file that is attached to the email and saves it in the folder created
        """
        msg = self.gmail.get(id=message, userId=user_id, format='full')
        # parts can be the message body, or attachments
        return msg
    
# Realization of the Gmail API interface
class Gmail(GmailServiceProvider):
    # Request all access (permission to read/send/receive emails, manage the inbox, and more)
    SCOPES = ['https://mail.google.com/']

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
                creds = flow.run_local_server(port=3000)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

    def list(self, userId='me', pageToken = None, maxResults = None):
        with self.service as service:
            return service.users().messages().list(userId=userId, pageToken=pageToken, maxResults = maxResults).execute()
    
    def get(self, id, userId='me', format='full'):
        try:
             result = self.service.users().messages().get(userId=userId, id=id, format = format).execute()   
        finally:
            self.service.close()
        return result
    
    def close(self):
        self.service.close()
