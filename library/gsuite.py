import datetime
import enum
import os
import pickle
from library import models, document_parser

# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
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
from googleapiclient.http import MediaIoBaseDownload
import json

# interface for the Gmail API wrapper
class GSuiteServiceProvider:

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
    count = 0
    def __init__(self, gmail: GSuiteServiceProvider):
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
        self.count += 1
        print(str(self.count) + ". Getting email with id " + msg_id + " for user " + user_id)
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

class GoogleSchemas(enum.Enum):

    GMAIL = 'gmail'
    CALENDAR = 'calendar'
    DRIVE = 'drive'
    DOCUMENTS = 'docs'

    @staticmethod
    def v(schema):
        if schema == GoogleSchemas.GMAIL:
            return 'v1'
        if schema == GoogleSchemas.CALENDAR:
            return 'v3'
        if schema == GoogleSchemas.DRIVE:
            return 'v3'
        if schema == GoogleSchemas.DOCUMENTS:
            return 'v1'
        return None    
    
# Realization of the Gmail API interface
class GSuite(GSuiteServiceProvider):
    # Request all access (permission to read/send/receive emails, manage the inbox, and more)
    SCOPES = ['https://mail.google.com/', 'https://www.googleapis.com/auth/calendar.readonly',
            'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']

    MIME_TYPE = {"pdf": "mimeType='application/pdf'",
                "docx": "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                "google_doc": "mimeType='application/vnd.google-apps.document'"}

    def service(self, google_schema: GoogleSchemas):
        credentials = self.__authenticate()
        return build(google_schema.value, GoogleSchemas.v(google_schema), credentials=credentials)

    def __init__(self, email, creds, docs_folder:str = "."):
        self.email = email
        self.creds = creds
        self.docs_folder = docs_folder

    def __authenticate(self):
        creds = None
        # the file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("INstalling creds", self.creds)
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds, self.SCOPES
                )
                creds = flow.run_local_server(port=3000)
            # save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds
        

    def list(self, userId='me', pageToken = None, maxResults = None):
        with self.service(GoogleSchemas.GMAIL) as service:
            return service.users().messages().list(userId=userId, pageToken=pageToken, maxResults = maxResults).execute()
    
    def get(self, id, userId='me', format='full'):
        with self.service(GoogleSchemas.GMAIL) as service:
             result = service.users().messages().get(userId=userId, id=id, format = format).execute()  
             self.__get_attachments(result, userId) 
    
        return result
    
    def events(self, now: datetime.datetime, count: int = 10):
        with self.service(GoogleSchemas.CALENDAR) as service:
            print("Getting the upcoming 10 events")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=count,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            print("events: ", events)            
            return events

    
    def __get_attachments(self, message: dict, userId='me'):
        attachments = []
        with self.service(GoogleSchemas.GMAIL) as service:
            for part in  message['payload'].get('parts',[]):
                filename = part.get('filename')      
                if filename:
                    attachmentId = part.get('body', {}).get('attachmentId')
                    attachment = service.users().messages().attachments().get(userId=userId, messageId=id, id=attachmentId).execute()
                    attachment['filename'] = filename
                    print("Attachment: " + str(filename))
                    attachments.append(attachment)

            if len(attachments) > 0:
                message['attachments'] = attachments


    def get_document_ids(self, type):
        with self.service(GoogleSchemas.DRIVE) as service:
            results = (
                service.files()
                .list(q = self.MIME_TYPE[type],
                    corpora='user',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True)
                .execute()
            )
            items = results.get("files", [])

            if not items:
                print("No files found.")
                return
            doc_ids = {}
            for item in items:
                doc_ids[item['id']] = item['name']
        return doc_ids

    def get_file_metadata(self, doc_id_name):
        metadata = {}
        doc_ids = list(doc_id_name.keys())
        with self.service(GoogleSchemas.DRIVE) as service:
            for doc in doc_ids:
                file_id = doc
                fields = 'id, name, mimeType, owners, lastModifyingUser, viewersCanCopyContent, createdTime, \
                modifiedTime, viewedByMeTime, sharedWithMeTime, permissions'
                file_metadata = service.files().get(fileId=file_id, fields=fields, supportsAllDrives=True).execute()
                file_metadata_cleaned = self.rename_id_field(file_metadata)
                metadata[doc] = file_metadata_cleaned
        return metadata
    
    def rename_id_field(self, file_metadata):
            file_metadata["metadata_id"] = file_metadata["id"]
            del file_metadata["id"]
            if "permissions" in file_metadata:
                for d in file_metadata["permissions"]:
                    d["permission_id"] = d["id"]
                    del d["id"] 
            return file_metadata

    def extract_content(self, doc_body):
        content = []
        for element in doc_body.get('content', []):
            if 'paragraph' in element:
                for para_element in element['paragraph'].get('elements', []):
                    if 'textRun' in para_element:
                        content.append(para_element['textRun']['content'])
        return ''.join(content)

    def get_gdocs_content(self, doc_ids_name):
        doc_ids = list(doc_ids_name.keys())
        with self.service(GoogleSchemas.DOCUMENTS) as service:
            doc_info = {}
            for doc in doc_ids:
            # Retrieve the documents contents from the Docs service.
                doc_structure = {}

                document = service.documents().get(documentId=doc).execute()
                text = self.extract_content(document.get('body'))

                doc_structure["text"] = text
                doc_structure["document_id"] = doc
                doc_info[doc] = doc_structure
        return doc_info
    
    def get_3p_content(self, doc_dict: dict, parser: document_parser.DocumentParser):

        print(" Getting 3p content for ", doc_dict.keys())
        with self.service(GoogleSchemas.DRIVE) as service:
            doc_info = {}
            for doc in doc_dict.keys():
                doc_structure = {}

                request = service.files().get_media(fileId=doc)
                target = os.path.join(self.docs_folder, doc_dict[doc])
                print("File target will be", target)
                fh = open(target, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download %d%%." % int(status.progress() * 100))
                doc = parser.parse(target)

                doc_structure["text"] = doc
                doc_structure["document_id"] = doc
                doc_info[doc] = doc_structure
        return doc_info

    def get_pdf_content(self, pdf_dict):
        return self.get_3p_content(pdf_dict, document_parser.PdfParser())
                
    def get_docx_content(self, docx_dict):
        return self.get_3p_content(docx_dict, document_parser.DocxParser())             

    def compile_info(self, document_type: str, content_callback: callable) -> dict:
        print("Compiling info for", document_type)
        gdoc_ids_name = self.get_document_ids(type=document_type)
        gdoc_metadata = self.get_file_metadata(gdoc_ids_name)
        gdoc_info = content_callback(gdoc_ids_name)
        print("     gdoc_info: ", gdoc_info.keys())
        doc_info = {} 
        for gdoc in gdoc_ids_name.keys():
            print("         gdoc id name: ", gdoc)
            if gdoc not in gdoc_info:
                print("Skipping ", gdoc, " as no content found in", gdoc_info.keys())
                continue
            doc_info[gdoc] = gdoc_info[gdoc]
            doc_info[gdoc]["metadata"] = gdoc_metadata[gdoc]
            doc_info[gdoc]["doc_type"] = document_type
        return doc_info

    def get_doc_info(self):
        doc_info = {}
        doc_info.update(self.compile_info("google_doc", self.get_gdocs_content))
        doc_info.update(self.compile_info("docx", self.get_docx_content))
        doc_info.update(self.compile_info("pdf", self.get_pdf_content))
        return doc_info



