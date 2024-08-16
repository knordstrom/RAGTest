import datetime
import enum
import os
from library import document_parser

# Gmail API utils
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.apps.meet_v2.services.conference_records_service import pagers
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from mimetypes import guess_type as guess_mime_type
import os
from googleapiclient.http import MediaIoBaseDownload

from google.apps import meet_v2
from google.apps.meet_v2.types import ConferenceRecord
from google.apps.meet_v2.types import resource

from library.models.api_models import ConferenceCall, ConferenceRecording, ConferenceSpace, ConferenceTranscript
from library.models import message

# interface for the Gmail API wrapper
class GSuiteServiceProvider:

    def service(self):
        pass

    def list_emails(self, userId: str = 'me', pageToken: str = None, maxResults: int = None) -> list[dict[str,str]]:
        pass

    def get_email(self, id: str, userId: str = 'me', format: str = 'full') -> message.Message:
        pass

    def close(self):
        pass
    

# Dependency Injectable Gmail methods
class GmailLogic:
    count = 0
    def __init__(self, gmail: GSuiteServiceProvider):
        self.gmail = gmail

    def get_emails(self, count: int = None) -> list[dict[str, str]]:
        pageToken: str = None
        messages_left: bool = True
        messages: list[dict[str, str]] = []

        while messages_left:
            results: list[dict[str,str]] = self.gmail.list_emails(userId='me', pageToken=pageToken, maxResults=count)
            pageToken = results.get('nextPageToken')
            new_messages = results.get('messages', [])
            count -= len(new_messages)
            messages += new_messages
            if not pageToken or (not count or count <= 0) or len(new_messages) == 0:               
                messages_left = False
        return messages
    
    def get_email(self, user_id: str='me', msg_id: str='') -> message.Message:
        self.count += 1
        print(str(self.count) + ". Getting email with id " + msg_id + " for user " + user_id)
        data = self.gmail.get_email(userId=user_id, id=msg_id)
        return message.Message.from_gsuite_payload(data)
    

    def read_message(self, user_id: str='me', message: str=''):
        """
        This function takes Gmail API `service` and the given `message_id` and does the following:
            - Downloads the content of the email
            - Prints email basic information (To, From, Subject & Date) and plain/text parts
            - Creates a folder for each email based on the subject
            - Downloads text/html content (if available) and saves it under the folder created as index.html
            - Downloads any file that is attached to the email and saves it in the folder created
        """
        msg = self.gmail.get_email(id=message, userId=user_id, format='full')
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
    
class GSuite(GSuiteServiceProvider):

    SCOPES: list[str] = ['https://mail.google.com/', 
              'https://www.googleapis.com/auth/calendar.readonly',
              'https://www.googleapis.com/auth/drive', 
              'https://www.googleapis.com/auth/documents',
              'https://www.googleapis.com/auth/meetings.space.readonly',
              'https://www.googleapis.com/auth/meetings.space.created'
              ]
    
    TOKEN_FILE: str = 'token.json'

    MIME_TYPE: dict[str, str] = {"pdf": "mimeType='application/pdf'",
                "docx": "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                "google_doc": "mimeType='application/vnd.google-apps.document'"}

    def service(self, google_schema: GoogleSchemas) -> Resource:
        credentials = self.__authenticate()
        print("Retrieved crednetials", credentials)
        return build(google_schema.value, GoogleSchemas.v(google_schema), credentials=credentials)
    
    _meet_client: meet_v2.ConferenceRecordsServiceAsyncClient = None
    @property
    def meet_client(self) -> meet_v2.ConferenceRecordsServiceAsyncClient:
        credentials = self.__authenticate()
        print("Retrieved credentials", credentials)
        if self._meet_client is None:
            self._meet_client = meet_v2.ConferenceRecordsServiceAsyncClient(credentials=credentials)
        return self._meet_client

    _spaces_client: meet_v2.SpacesServiceAsyncClient = None
    @property
    def meet_spaces_client(self) -> meet_v2.SpacesServiceAsyncClient:
        credentials = self.__authenticate()
        print("Retrieved credentials", credentials)
        if self._spaces_client is None:
            self._spaces_client = meet_v2.SpacesServiceAsyncClient(credentials=credentials)
        return self._spaces_client

    def __init__(self, email, creds, docs_folder:str = "."):
        self.email = email
        self.creds = creds
        self.docs_folder = docs_folder

    def __authenticate(self):
        creds = None
        # the file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists(self.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)

        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds, self.SCOPES
                )
                creds = flow.run_local_server(
                    # open_browser=False, 
                    # bind_addr="0.0.0.0", port=3000
                    port=3000
                    )
            # save the credentials for the next run
            with open(self.TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        return creds
        

    def list_emails(self, userId: str='me', pageToken: str = None, maxResults: int = None) -> list[dict[str,str]]:
        with self.service(GoogleSchemas.GMAIL) as service:
            return service.users().messages().list(userId=userId, pageToken=pageToken, maxResults = maxResults).execute()
    
    def get_email(self, id: str, userId: str='me', format: str='full') -> dict[str, str]:
        with self.service(GoogleSchemas.GMAIL) as service:
             result = service.users().messages().get(userId=userId, id=id, format = format).execute()  
             self.__get_attachments(result, userId) 
    
        return result
    
    def events(self, now: datetime.datetime, count: int = 10) -> list[dict[str, str]]:
        service: Resource
        with self.service(GoogleSchemas.CALENDAR) as service:
            print("Getting the upcoming 10 events")
            events_result: dict[str, any] = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    eventTypes="default",
                    maxResults=count,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            for event in events:
                event['source'] = 'gmail'
            print("events: ", events)            
            return events

    
    def __get_attachments(self, message: dict[str, any], userId: str='me') -> None:
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

    async def list_meetings(self, count: int = 10) -> list[ConferenceCall]:
        request = meet_v2.ListConferenceRecordsRequest()
        page_result: pagers.ListConferenceRecordsAsyncPager = await self.meet_client.list_conference_records(request=request)
        
        result: list[dict[str, any]] = []
        async for response in page_result:
            space = await self.get_space(response.space)
            recordings = await self.list_recordings(response.name)
            transcripts = await self.list_transcripts(response.name, space, count=10)

            call: ConferenceCall = ConferenceCall.from_protobuf(response, space, recordings, transcripts)
            result.append(call)     
        return result
    
    async def list_recordings(self, conference_name: str) -> ConferenceRecording:
        client = self.meet_client
        request = meet_v2.ListRecordingsRequest( parent=conference_name)
        page_result: pagers.ListRecordingsAsyncPager = await client.list_recordings(request=request)

        result = []
        async for response in page_result:
            result.append(ConferenceRecording.from_protobuf(response))
        return result
    
    async def get_space(self, space_name: str) -> ConferenceSpace:
        client = self.meet_spaces_client
        request = meet_v2.GetSpaceRequest(
            name=space_name,
        )
        response: resource.Space = await client.get_space(request=request)
        return ConferenceSpace.from_protobuf(response)

    async def list_transcripts(self, parent_value: str, space: ConferenceSpace, count: int = 10) -> list[ConferenceTranscript]:
        request = meet_v2.ListTranscriptsRequest(
            parent=parent_value, 
            page_size=count
        )
        page_result: pagers.ListTranscriptsAsyncPager = await self._meet_client.list_transcripts(request=request)
        result = []
        async for response in page_result:
            result.append(ConferenceTranscript.from_protobuf(response, space))
        return result

    def get_document_ids(self, type: str) -> dict[str, str]:
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

    def get_file_metadata(self, doc_id_name: dict[str, any]) -> dict[str, dict[str, any]]:
        metadata: dict[str, dict[str, any]] = {}
        doc_ids: list[str] = list(doc_id_name.keys())
        with self.service(GoogleSchemas.DRIVE) as service:
            for doc in doc_ids:
                file_id = doc
                fields = 'id, name, mimeType, owners, lastModifyingUser, viewersCanCopyContent, createdTime, \
                modifiedTime, viewedByMeTime, sharedWithMeTime, permissions'
                file_metadata = service.files().get(fileId=file_id, fields=fields, supportsAllDrives=True).execute()
                file_metadata_cleaned = self.rename_id_field(file_metadata)
                metadata[doc] = file_metadata_cleaned
        return metadata
    
    def rename_id_field(self, file_metadata: dict[str, any]) -> dict[str, any]:
            file_metadata["metadata_id"] = file_metadata["id"]
            del file_metadata["id"]
            if "permissions" in file_metadata:
                for d in file_metadata["permissions"]:
                    d["permission_id"] = d["id"]
                    del d["id"] 
            return file_metadata

    def extract_content(self, doc_body: str) -> str:
        content = []
        for element in doc_body.get('content', []):
            if 'paragraph' in element:
                for para_element in element['paragraph'].get('elements', []):
                    if 'textRun' in para_element:
                        content.append(para_element['textRun']['content'])
        return ''.join(content)

    def get_gdocs_content(self, doc_ids_name: dict) -> dict[str, any]:
        doc_ids = list(doc_ids_name.keys())
        with self.service(GoogleSchemas.DOCUMENTS) as service:
            doc_info: dict[str, any] = {}
            for doc in doc_ids:
                doc_structure: dict[str, any] = {}
                document: dict[str, any] = service.documents().get(documentId=doc).execute()
                text = self.extract_content(document.get('body'))

                doc_structure["text"] = text
                doc_structure["document_id"] = doc
                doc_info[doc] = doc_structure
        return doc_info
    
    def get_3p_content(self, doc_dict: dict[str, any], parser: document_parser.DocumentParser) -> dict[str, any]:

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

    def get_pdf_content(self, pdf_dict: dict[str, any]) -> dict[str, any]:
        return self.get_3p_content(pdf_dict, document_parser.PdfParser())
                
    def get_docx_content(self, docx_dict: dict[str, any]) -> dict[str, any]:
        return self.get_3p_content(docx_dict, document_parser.DocxParser())             

    def compile_info(self, document_type: str, content_callback: callable) -> dict[str, any]:
        print("Compiling info for", document_type)
        gdoc_ids_name = self.get_document_ids(type=document_type)
        if not gdoc_ids_name:
            print("Missing gdocs name for ", document_type)
            return {}
        gdoc_metadata = self.get_file_metadata(gdoc_ids_name)
        gdoc_info = content_callback(gdoc_ids_name)
        print("     gdoc_info: ", gdoc_info.keys())
        doc_info: dict[str, any] = {} 
        for gdoc in gdoc_ids_name.keys():
            print("         gdoc id name: ", gdoc)
            if gdoc not in gdoc_info:
                print("Skipping ", gdoc, " as no content found in", gdoc_info.keys())
                continue
            doc_info[gdoc] = gdoc_info[gdoc]
            doc_info[gdoc]["metadata"] = gdoc_metadata[gdoc]
            doc_info[gdoc]["doc_type"] = document_type
        return doc_info

    def get_doc_info(self) -> dict[str, any]:
        doc_info: dict[str, any] = {}
        doc_info.update(self.compile_info("google_doc", self.get_gdocs_content))
        doc_info.update(self.compile_info("docx", self.get_docx_content))
        doc_info.update(self.compile_info("pdf", self.get_pdf_content))
        return doc_info



