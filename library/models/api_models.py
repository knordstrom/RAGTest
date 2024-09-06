from datetime import datetime
from uuid import UUID
from pydantic import AliasChoices, BaseModel, EmailStr, Field, ConfigDict

from typing import List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, Field, fields as dataclassFields
from google.apps.meet_v2.types import ConferenceRecord, Recording
from google.apps.meet_v2.types import resource


T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    @staticmethod
    def create(response: T):
        return ApiResponse.model_validate({'response':response})

    response: T
    timestamp: datetime = datetime.now()
    paging: Optional[dict] = None
    
## /ask
class AskRequestContext(BaseModel):
    emails: List[str]

class AskResponse(BaseModel):
    question: str
    response: str
    context: AskRequestContext

## /briefs
class SlackConversationEntry(BaseModel):
    text: str 
    thread_id: str 
    channel_id: str 
    summary: str 
    last_response: datetime
    importance: Optional[float] = None

class EmailConversationEntry(BaseModel):
    text: str 
    thread_id: str 
    summary: str 
    last_response: datetime
    importance: Optional[float] = None

class DocumentMetadata(BaseModel):
    created_time: datetime 
    metadata_id: str 
    modified_time: datetime 
    mime_type: str 
    name: str 
    last_response: datetime

class DocumentEntry(BaseModel):
    document_id: str 
    doc_type: str 
    metadata: DocumentMetadata 
    provider: Optional[str] = None
    summary: str 
    importance: Optional[float] = None

class TranscriptEntry(BaseModel):
    document_id: str 
    meeting_code: str 
    provider: Optional[str] = None 
    title: str 
    attendee_names: List[str] 
    summary: str

class MeetingSupport(BaseModel):
    docs: List[DocumentEntry] = []
    email: List[EmailConversationEntry] = []
    slack: List[SlackConversationEntry] = []
    calls: List[TranscriptEntry] = []

class MeetingAttendee(BaseModel):
    email: EmailStr 
    name: str 
    status: Optional[str] = None

class MeetingContext(BaseModel):
    attendees: list[MeetingAttendee] 
    start: datetime 
    end: datetime 
    description: Union[str, None] = None 
    recurring_id: str 
    name: str 
    person: MeetingAttendee 
    organizer: MeetingAttendee 
    support: MeetingSupport 

class BriefContext(BaseModel):
    schedule: List[MeetingContext] 

class BriefResponse(BaseModel):
    email: EmailStr 
    start_time: datetime 
    end_time: datetime 
    summary: str 
    context:BriefContext 

## /schedule

class Meeting(BaseModel):
    attendees: List[MeetingAttendee] 
    start: datetime 
    end: datetime 
    description: Union[str, None] = None
    recurring_id: str 
    name: str
    location: Optional[str] = None
    person: Optional[MeetingAttendee] = None
    organizer: MeetingAttendee

class ScheduleResponse(BaseModel):
    email: EmailStr 
    start_time: datetime 
    end_time: datetime 
    events: List[Meeting]

## /references

class EmailMessage(BaseModel):
    email_id: str
    history_id: str
    thread_id: str
    labels: List[str]
    to: List[MeetingAttendee]
    cc: List[MeetingAttendee]
    bcc: List[MeetingAttendee]
    subject: str
    sender: MeetingAttendee 
    date: datetime
    provider: str
    text: List[str] = []

class EmailThreadResponse(BaseModel):
    cc: List[MeetingAttendee]
    subject: str
    date: datetime
    labels: List[str]
    to: List[MeetingAttendee]
    sender: MeetingAttendee 
    thread_id: str

    
class DocumentPermission(BaseModel):
    type: str
    kind: str
    pendingOwner: bool = False
    displayName: Union[str, None] = None
    role: str
    photoLink: str = None
    emailAddress: Union[EmailStr, None] = None
    permission_id: str
    deleted: bool = False

class DocumentOwner(BaseModel):
    photoLink: str = None
    displayName: Union[str, None] = None
    emailAddress: Union[EmailStr, None] = None
    kind: str
    permissionId: Union[str, None] = None

class DocumentResponseMetadata(BaseModel):
    createdTime: datetime
    metadata_id: str
    owners: List[DocumentOwner] = []
    lastModifyingUser: DocumentOwner
    modifiedTime: datetime
    viewersCanCopyContent: bool
    mimeType: str
    permissions: List[DocumentPermission] = []
    name: str

class DocumentResponse(BaseModel):
    provider: Union[str, None] = "google"
    doc_type: str
    document_id: str
    metadata: DocumentResponseMetadata
    text: List[str] = []
    summary: Union[str, None] = None


class SlackMessage(BaseModel):
    sender: EmailStr
    thread_id: str
    ts: datetime
    type: str
    subtype: Union[str, None] = None
    message_id: str
    text: List[str] = []


class SlackResponse(BaseModel):
    messages: List[SlackMessage]

class SlackThreadResponse(BaseModel):
    channel_id: str
    thread_id: str
    messages: List[SlackMessage] = []

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: Optional[str] = None
    email: EmailStr
    expiry: Optional[datetime] = None

class ConferenceSpace(BaseModel):
    name: str
    meeting_uri: str
    meeting_code: str
    access_type: str
    entry_point_access: str

    @staticmethod
    def from_protobuf(pb: resource.Space) -> 'ConferenceSpace':
        return ConferenceSpace(name = pb.name, meeting_uri = pb.meeting_uri, 
                                meeting_code = pb.meeting_code, access_type = pb.config.access_type.name, 
                                entry_point_access = pb.config.entry_point_access.name)

class ConferenceTranscript(BaseModel):
    name: str
    document: str
    export_uri: str
    start_time: datetime
    end_time: datetime
    space: ConferenceSpace

    @staticmethod
    def from_protobuf(pb: resource.Transcript, space: ConferenceSpace) -> 'ConferenceTranscript':
        print("Transcript", pb)
        return ConferenceTranscript(name = pb.name, document = pb.docs_destination.document,      
                                    export_uri = pb.docs_destination.export_uri, space = space,                          
                                    start_time = pb.start_time, end_time = pb.end_time)

class ConferenceRecording(BaseModel):
    start_time: datetime
    end_time: datetime
    file: str
    export_uri: str

    @staticmethod
    def from_protobuf(pb: Recording) -> 'ConferenceRecording':
        return ConferenceRecording(start_time = pb.start_time, end_time = pb.end_time, 
                                   file = pb.drive_destination.file, 
                                   export_uri = pb.drive_destination.export_uri)

class ConferenceCall(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    expire_time: datetime
    recordings: List[ConferenceRecording]
    space: ConferenceSpace
    transcripts: List[ConferenceTranscript]

    @staticmethod
    def from_protobuf(pb: ConferenceRecord, space: ConferenceSpace, recordings: list[ConferenceRecording],
                      transcripts: list[ConferenceTranscript]) -> 'ConferenceCall':
        return ConferenceCall(name = pb.name, start_time = pb.start_time, 
                                end_time = pb.end_time, expire_time = pb.expire_time, space=space, 
                                recordings = recordings, transcripts = transcripts)
    
class TranscriptLine(BaseModel):
    speaker: str
    text: str
    ordinal: int

class TranscriptConversation(BaseModel):
    transcript_id: str
    meeting_code: str
    provider: str
    title: str
    attendee_names: List[str]
    conversation: list[TranscriptLine]

    @staticmethod
    def from_weaviate_properties(props: dict[str, str], conversation: list[TranscriptEntry] = []) -> 'TranscriptConversation':
        return TranscriptConversation(
                transcript_id=props.get('document_id'),
                meeting_code=props.get('meeting_code'),
                provider=props.get('provider'),
                title=props.get('title'),
                attendee_names=props.get('attendee_names'),
                conversation=conversation
            )
    
class SlackUser(BaseModel):
    id: str
    name: str
    real_name: str
    email: EmailStr
    is_bot: bool
    deleted: bool