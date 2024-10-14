from datetime import datetime
import enum
from typing import Any, Optional, TypeVar, Union
from pydantic import BaseModel, Field, FieldSerializationInfo
from pydantic.fields import FieldInfo
from typing import get_origin
from weaviate.classes.config import Property, DataType
import weaviate.classes as wvc

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)

class WeaviateSchemas(enum.Enum):
    EMAIL_THREAD = 'email_thread'
    EMAIL = 'email'
    EMAIL_TEXT = 'email_text'
    EVENT = 'event'
    EVENT_TEXT = 'event_text'
    EMAIL_THREAD_SUMMARY = 'email_thread_summary'
    DOCUMENT = 'document'
    DOCUMENT_TEXT = 'document_text'
    DOCUMENT_SUMMARY = 'document_summary'
    SLACK_CHANNEL = 'slack_channel'
    SLACK_THREAD = 'slack_thread'
    SLACK_MESSAGE = 'slack_message'
    SLACK_MESSAGE_TEXT = 'slack_message_text'
    SLACK_THREAD_SUMMARY = 'slack_thread_summary'
    TRANSCRIPT = 'transcript'
    TRANSCRIPT_ENTRY = 'transcript_entry'
    TRANSCRIPT_SUMMARY = 'transcript_summary'

    @staticmethod
    def summary_prompt_key(schema: 'WeaviateSchemas') -> str:
        if schema == WeaviateSchemas.EMAIL_THREAD_SUMMARY:
            return 'Summarizer.email_summarizer'
        elif schema == WeaviateSchemas.DOCUMENT_SUMMARY:
            return None
        elif schema == WeaviateSchemas.SLACK_THREAD_SUMMARY:
            return "BriefingSupport.slack_context_for"
        elif schema == WeaviateSchemas.TRANSCRIPT_SUMMARY:
            return "BriefingSupport.transcript_context_for"
        return None

class WeaviateSchemaTransformer:
    @staticmethod
    def data_type(tpe: FieldInfo) -> DataType:
        # print("             Data type: ", tpe.annotation, tpe , get_origin(tpe.annotation) is list)
        if tpe.annotation == datetime:
            return DataType.DATE
        elif tpe.annotation == int:
            return DataType.INT
        elif tpe.annotation == bool:
            return DataType.BOOL
        elif tpe.annotation == float:
            return DataType.NUMBER
        elif tpe.annotation == list[datetime]:
            return DataType.DATE_ARRAY
        elif tpe.annotation == list[str]:
            return DataType.TEXT_ARRAY
        elif tpe.annotation == list[int]:
            return DataType.INT_ARRAY
        elif tpe.annotation == list[bool]:
            return DataType.BOOL_ARRAY
        elif tpe.annotation == list[float]:
            return DataType.NUMBER_ARRAY
        elif tpe.annotation == str:
            return DataType.TEXT
        elif get_origin(tpe.annotation) is list:
            return DataType.OBJECT_ARRAY
        elif get_origin(tpe.annotation) is Union:
            return WeaviateSchemaTransformer.data_type(FieldInfo(annotation=tpe.annotation.__args__[0]))
        else:
            return DataType.OBJECT

    @staticmethod
    def to_prop(dt: DataType, name: str, field: FieldInfo) -> Property:
        name = name.strip("_")
        if dt == DataType.OBJECT_ARRAY:
            inner_type = field.annotation.__args__[0]
            return Property(name=name, data_type=dt, nested_properties= WeaviateSchemaTransformer.to_props(inner_type)         ) 
        elif dt == DataType.OBJECT:
            return  Property(name=name, data_type=dt, nested_properties=  WeaviateSchemaTransformer.to_props(field.annotation)) 
        else:
            return Property(name=name, data_type=dt)    
        
    @staticmethod
    def to_props(obj: T) -> list[Property]:
        result = []
        for name, field in dict(obj.model_fields).items():
            dt = WeaviateSchemaTransformer.data_type(field)
            p = WeaviateSchemaTransformer.to_prop(dt, name, field)
            result.append(p)

        return result
    
class CommunicationSummary(BaseModel):
    text: str
    thread_id: str
    summary_date: datetime

class CommunicationSummaryAndConversation(BaseModel):
    summary: CommunicationSummary
    conversation: str

class CommunicationEntry(BaseModel):
    text: str
    sender: str
    entry_date: datetime

class EmailThread(BaseModel):
    thread_id: str
    latest: datetime

class EmailParticipant(BaseModel):
    email: str
    name: str

class Email(BaseModel):
    email_id: str
    history_id: Union[str, None] = None
    thread_id: str
    labels: list[str]
    to: list[EmailParticipant]
    cc: list[EmailParticipant] = Field(default=[])
    bcc: list[EmailParticipant] = Field(default=[])
    subject: str
    sender: EmailParticipant
    date: datetime
    provider: str
    person_id: str

class EmailText(BaseModel):
    text: str
    email_id: str
    thread_id: str
    ordinal: int
    date: datetime

class EmailThreadSummary(CommunicationSummary):
    text: str
    thread_id: str
    summary_date: datetime

class EmailTextWithFrom(BaseModel):
    text: str
    email_id: str
    thread_id: str
    ordinal: int
    date: datetime
    sender: EmailParticipant

class EmailConversationWithSummary(BaseModel):
    thread_id: str
    conversation: str
    summary: str
    last_response: datetime

class Event(BaseModel):
    event_id: str
    summary: str
    location: Optional[str]
    start: datetime
    end: datetime
    email_id: str
    sent_date: datetime
    sender: str
    to: str
    thread_id: str
    name: str
    description: str
    provider: str

class EventText(BaseModel):
    text: str
    event_id: str
    ordinal: int

class DocumentPermission(BaseModel):
    kind: str
    permission_id: str
    type: str
    emailAddress: str
    role: str
    displayName: str
    photoLink: str
    deleted: bool
    pendingOwner: bool

class DocumentUser(BaseModel):
    kind: str
    displayName: str
    photoLink: str
    me: bool
    permissionId: str
    emailAddress: str
    
class DocumentMetadata(BaseModel):
    metadata_id: str
    name: str
    mimeType: str
    viewedByMeTime: datetime
    createdTime: datetime
    modifiedTime: datetime
    owners: list[DocumentUser]
    lastModifyingUser: DocumentUser
    viewersCanCopyContent: bool
    permissions: list[DocumentPermission]
    provider: str

class Document(BaseModel):
    document_id: str
    metadata: DocumentMetadata
    doc_type: str
    latest: datetime

class DocumentText(BaseModel):
    text: str
    document_id: str
    ordinal: int

class DocumentSummary(CommunicationSummary):
    text: str
    document_id: str
    summary_date: datetime

    def __init__(self, text: str, document_id: str, summary_date: datetime):
        self.document_id = document_id
        self.thread_id = document_id
        self.text = text
        self.summary_date = summary_date

class SlackChannel(BaseModel):
    channel_id: str
    name: str
    creator: str
    is_private: bool
    is_shared: bool
    num_members: int
    updated: datetime
    provider: str

class SlackThread(BaseModel):
    thread_id: str
    channel_id: str
    latest: datetime

class SlackMessage(BaseModel):
    message_id: str
    sender: str
    subtype: str
    ts: datetime
    type: str
    thread_id: str

class SlackMessageText(BaseModel):
    text: str
    message_id: str
    thread_id: str
    ordinal: int

class SlackThreadSummary(CommunicationSummary):
    text: str
    thread_id: str
    summary_date: datetime

class Transcript(BaseModel):
    document_id: str
    meeting_code: str
    title: str
    provider: str
    attendee_names: list[str]

class TranscriptEntry(BaseModel):
    meeting_code: str
    speaker: str
    text: str
    ordinal: int

class TranscriptSummary(CommunicationSummary):
    text: str
    meeting_code: str
    summary_date: datetime

    def __init__(self, text: str, meeting_code: str, summary_date: datetime):
        super().__init__(text=text, thread_id=meeting_code, summary_date=summary_date, meeting_code = meeting_code)
        # self.meeting_code = meeting_code
    
class WeaviateSchema:

    class_objs: list[(WeaviateSchemas,dict[str, any])] = [
        (WeaviateSchemas.EMAIL_THREAD, {  
            "class": "EmailThread",    
            "properties": WeaviateSchemaTransformer.to_props(EmailThread),
            "references": [],
            "vectorizer": False,
        }),
        (WeaviateSchemas.EMAIL,{
            "class": "Email",
            "properties": WeaviateSchemaTransformer.to_props(Email),       
            "references": [],
            "vectorizer": False,   
        }),
        (WeaviateSchemas.EMAIL_TEXT, {
                "class": "EmailText",
                "properties": WeaviateSchemaTransformer.to_props(EmailText),       
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.EMAIL_THREAD_SUMMARY, {
                "class": "EmailThreadSummary",
                "properties": WeaviateSchemaTransformer.to_props(EmailThreadSummary),       
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.EVENT, {
                # Class definition
                "class": "Event",
                "properties": WeaviateSchemaTransformer.to_props(Event),       
                "references": [],
                "vectorizer": False,
        }),
        (WeaviateSchemas.EVENT_TEXT, {
                "class": "EventText",
                "properties": WeaviateSchemaTransformer.to_props(EventText),
                "references": [ ],
                "vectorizer": True,
        }),
        (WeaviateSchemas.DOCUMENT, {
            "class": "Document",
            "properties": WeaviateSchemaTransformer.to_props(Document),
            "references": [],
            "vectorizer": False,
        }),
        (WeaviateSchemas.DOCUMENT_TEXT, {
                "class": "DocumentText",
                "properties": WeaviateSchemaTransformer.to_props(DocumentText),
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.DOCUMENT_SUMMARY, {
                "class": "DocumentSummary",
                "properties": WeaviateSchemaTransformer.to_props(DocumentSummary),
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.SLACK_CHANNEL, { 
            "class": "SlackChannel",    
            "properties": WeaviateSchemaTransformer.to_props(SlackChannel),
            "references": [],
            "vectorizer": False,
        }),
        (WeaviateSchemas.SLACK_THREAD, {  
            "class": "SlackThread",    
            "properties": WeaviateSchemaTransformer.to_props(SlackThread),
            "references": [ ],
            "vectorizer": False,
        }),
        (WeaviateSchemas.SLACK_MESSAGE, {   
                "class": "SlackMessage",
                "properties": WeaviateSchemaTransformer.to_props(SlackMessage),
                "references": [],
                "vectorizer": False,
        }),
        (WeaviateSchemas.SLACK_MESSAGE_TEXT, {   
                "class": "SlackMessageText",
                "properties": WeaviateSchemaTransformer.to_props(SlackMessageText),
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.SLACK_THREAD_SUMMARY, {
                "class": "SlackThreadSummary",
                "properties": WeaviateSchemaTransformer.to_props(SlackThreadSummary),       
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.TRANSCRIPT, {   
                "class": "Transcript",
                "properties": WeaviateSchemaTransformer.to_props(Transcript),
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.TRANSCRIPT_ENTRY, {   
                "class": "TranscriptEntry",
                "properties": WeaviateSchemaTransformer.to_props(TranscriptEntry),
                "references": [],
                "vectorizer": True,
        }),
        (WeaviateSchemas.TRANSCRIPT_SUMMARY, {
                "class": "TranscriptSummary",
                "properties": WeaviateSchemaTransformer.to_props(TranscriptSummary),       
                "references": [],
                "vectorizer": True,
        })
    ]
    
    class_map: dict[WeaviateSchemas,dict[str, any]] = dict(class_objs)

