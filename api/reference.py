from typing import Annotated, List

from fastapi.security import OAuth2PasswordBearer

from library.managers.auth_manager import AuthManager
from library.models.api_models import ApiResponse, DocumentResponse, EmailMessage, EmailThreadResponse, SlackMessage, SlackResponse, SlackThreadResponse, TranscriptConversation
from library.managers.api_support import APISupport

from library.data.local.weaviate import Weaviate
from library.models.employee import Employee, User
from library.models.weaviate_schemas import WeaviateSchemas
from fastapi import APIRouter, Depends
from library.models.weaviate_schemas import WeaviateSchemas
from fastapi import APIRouter

route = APIRouter(tags=["References"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login/openapi")

@route.get('/references/email/messages')
async def email_messages(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[List[EmailMessage]]:  
    """Retrieve email messages for the current user."""
    w: Weaviate = Weaviate()  
    return ApiResponse.create(w.get_emails(me))

@route.get('/references/email/messages/{email_id}')
async def email_message(email_id:str,
                        me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[EmailMessage]:  
    """Retrieve an email message by id for the current user."""
    w: Weaviate = Weaviate()  
    response: EmailMessage = w.get_email_by_id(email_id)

    APISupport.assert_not_none(response, f"Email with id {email_id} not found")
    AuthManager.assert_authorization_email(me, response.all_emails)

    return ApiResponse.create(response)

@route.get('/references/email/thread/{thread_id}')
async def email_thread(thread_id:str,
                       me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))])-> ApiResponse[EmailThreadResponse]: 
    """Retrieve metadata for an email thread by id for the current user."""
    w: Weaviate = Weaviate()   
    result: EmailThreadResponse = w.get_thread_by_id(thread_id)

    APISupport.assert_not_none(result, f"Thread with id {thread_id} not found")
    AuthManager.assert_authorization_email(me, result.all_emails)

    return ApiResponse.create(result) if result else APISupport.error_response(404, f"Thread with id {thread_id} not found")

@route.get('/references/slack/messages')
async def slack_messages(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[SlackResponse]:   
    """Retrieve slack messages for the current user."""
    w: Weaviate = Weaviate()
    messages: SlackResponse = w.get_slack_messages(me)
    allowed_messages = []
    threads: dict[str, SlackThreadResponse] = {}
    for message in messages.messages:
        thread = threads.get(message.thread_id)
        if not thread:
            thread = w.get_slack_thread_by_id(message.thread_id)
            threads[message.thread_id] = thread

        if thread and thread.is_authorized(me):
            allowed_messages.append(message)
    return ApiResponse.create(w.get_slack_messages(me))

@route.get('/references/slack/messages/{message_id}')
async def slack_message(message_id:str,
                        me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[SlackMessage]:   
    """Retrieve a slack message by id for the current user."""
    w: Weaviate = Weaviate()
    results = w.get_slack_message_by_id(message_id)
    if not results:
        return APISupport.error_response(404, f"Message with id {message_id} not found")
    thread = w.get_slack_thread_by_id(results.thread_id)
    if not thread or not thread.is_authorized(me):
        return APISupport.error_response(403, f"User {me.email} is not authorized to view message {message_id}")
    return ApiResponse.create(results)
    
@route.get('/references/slack/thread/{thread_id}')
async def slack_thread(thread_id: str,
                       me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[SlackThreadResponse]:
    """Retrieve metadata for a slack thread by id for the current user."""
    w: Weaviate = Weaviate()   
    result = w.get_slack_thread_by_id(thread_id)
    if not result:
        return APISupport.error_response(404, f"Thread with id {thread_id} not found")
    if not result.is_authorized(me):
        return APISupport.error_response(403, f"User {me.email} is not authorized to view thread {thread_id}")
    return ApiResponse.create(result) 

@route.get('/references/slack/thread/{thread_id}/messages')
async def slack_thread_messages(thread_id: str,
                                me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[SlackThreadResponse]: 
    """Retrieve messages for a slack thread by id for the current user."""
    w: Weaviate = Weaviate()
    results = w.get_slack_thread_messages_by_id(thread_id)
    if not results:
        return APISupport.error_response(404, f"Thread with id {thread_id} not found")
    if not results.is_authorized(me):
        return APISupport.error_response(403, f"User {me.email} is not authorized to view thread {thread_id}")
    return ApiResponse.create(results) 

@route.get('/references/documents')
async def documents(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[List[DocumentResponse]]:      
    """Retrieve documents for the current user."""
    w: Weaviate = Weaviate()
    docs = w.get_documents()
    results = [x for x in docs if x.metadata.is_authorized(me)]
    return ApiResponse.create(results)

@route.get('/references/documents/{document_id}')
async def document(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))], document_id: str) -> ApiResponse[DocumentResponse]:      
    """Retrieve a document by id for the current user."""
    w: Weaviate = Weaviate()
    result: DocumentResponse = w.get_document_by_id(document_id)
    if not result:
        return APISupport.error_response(404, f"Document with id {document_id} not found")

    if not result.metadata.is_authorized(me):
        return APISupport.error_response(403, f"User {me.email} is not authorized to view document {document_id}")
    return ApiResponse.create(result)

@route.delete('/references/armageddon/{collection}') #, include_in_schema=False
async def armaggedon(collection: str,
                     me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> str:
    """Truncate a collection in Weaviate."""
    w: Weaviate = Weaviate()
    w.truncate_collection(WeaviateSchemas[collection])
    return f"Collection {collection} truncated"

@route.get('/references/conferences/transcripts')
async def conference_transcripts(me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[List[TranscriptConversation]]:
    """Retrieve a list of transcripts for meetings involving the current user."""
    w: Weaviate = Weaviate()
    conversations = w.get_transcript_conversations()
    results = [x for x in conversations if x.is_authorized(me)]
    return ApiResponse.create(results)

@route.get('/references/conferences/transcripts/{meeting_code}')
async def conference_transcript_by_meeting_code(meeting_code: str,
                                                me: Annotated[User, Depends(AuthManager.get_user_dependency(oauth2_scheme))]) -> ApiResponse[TranscriptConversation]:
    """Retrieve transcripts for a conference by meeting code for the current user."""
    w: Weaviate = Weaviate()
    results: TranscriptConversation = w.get_transcript_conversation_by_meeting_code(meeting_code)
    if not results:
        return APISupport.error_response(404, f"Transcripts for meeting code {meeting_code} not found")
    
    if not results.is_authorized(me):
        return APISupport.error_response(403, f"User {me.email} is not authorized to view transcripts for meeting code {meeting_code}")
    
    return ApiResponse.create(results)