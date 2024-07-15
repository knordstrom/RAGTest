from datetime import datetime
from uuid import UUID
from flask_restx import Api, fields
from pydantic import AliasChoices, BaseModel, EmailStr, Field, ConfigDict

import typing
from typing import List, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, Field, fields as dataclassFields
from flask_restx import fields as flaskRPFields



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
class SlackEntry(BaseModel):
    text: str 
    thread_id: str 
    ordinal: int 
    message_id: str 
    channel_id: str 
    summary: str 

class EmailEntry(BaseModel):
    text: str 
    email_id: str 
    ordinal: int 
    thread_id: str 
    summary: str 

class DocumentMetadata(BaseModel):
    createdTime: datetime 
    metadata_id: str 
    modifiedTime: datetime 
    mimeType: str 
    name: str 

class DocumentEntry(BaseModel):
    document_id: str 
    doc_type: str 
    metadata: DocumentMetadata 
    provider: Optional[str] = None
    summary: str 

class MeetingSupport(BaseModel):
    docs: List[DocumentEntry] 
    email: List[EmailEntry] 
    slack: List[SlackEntry] 

class MeetingAttendee(BaseModel):
    email: EmailStr 
    name: str 
    status: Optional[str] = None

class MeetingContext(BaseModel):
    attendees: list[MeetingAttendee] 
    start: datetime 
    end: datetime 
    description: str 
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
    person: MeetingAttendee
    organizer: MeetingAttendee

class ScheduleResponse(BaseModel):
    email: EmailStr 
    start_time: datetime 
    end_time: datetime 
    events: List[Meeting]

## /references

class EmailMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True, fields = {
            'sender': 'from'
        })

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