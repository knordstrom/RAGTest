import datetime
import json
from typing import List, Union
import flask

from library.api_models import ApiResponse, DocumentResponse, EmailMessage, EmailThreadResponse, SlackMessage, SlackResponse, SlackThreadResponse
from library.apisupport import APISupport
from library.gsuite import GSuite
from library.slack import Slack, SlackAuthException
from googleapiclient.errors import HttpError

from library.weaviate import Weaviate
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sort
from fastapi import APIRouter

route = APIRouter(tags=["References"])

@route.get('/references/email/messages')
async def email_messages() -> ApiResponse[List[EmailMessage]]:  
    """Retrieve email messages for the current user."""
    w = Weaviate()  
    return ApiResponse.create(w.get_emails())

@route.get('/references/email/messages/{email_id}')
async def email_message(email_id:str) -> ApiResponse[EmailMessage]:  
    """Retrieve an email message by id for the current user."""
    w = Weaviate()  
    response = w.get_email_by_id(email_id)
    return ApiResponse.create(response) if response else flask.abort(404, f"Email with id {email_id} not found")
    
@route.get('/references/email/thread/{thread_id}')
async def email_thread(thread_id:str)-> ApiResponse[EmailThreadResponse]: 
    """Retrieve metadata for an email thread by id for the current user."""
    w = Weaviate()   
    result = w.get_thread_by_id(thread_id)
    return ApiResponse.create(result) if result else flask.abort(404, f"Thread with id {thread_id} not found")

@route.get('/references/slack/messages')
async def slack_messages() -> ApiResponse[SlackResponse]:   
    """Retrieve slack messages for the current user."""
    w = Weaviate()
    return ApiResponse.create(w.get_slack_messages())

@route.get('/references/slack/messages/{message_id}')
async def slack_message(message_id:str) -> ApiResponse[SlackMessage]:   
    """Retrieve a slack message by id for the current user."""
    w = Weaviate()
    results = w.get_slack_message_by_id(message_id)
    return ApiResponse.create(results) if results else flask.abort(404, f"Message with id {message_id} not found")
    
@route.get('/references/slack/thread/{thread_id}')
async def slack_thread(thread_id: str) -> ApiResponse[SlackThreadResponse]:
    """Retrieve metadata for a slack thread by id for the current user."""
    w = Weaviate()   
    result = w.get_slack_thread_by_id(thread_id)
    return ApiResponse.create(result) if result else flask.abort(404, f"Thread with id {thread_id} not found")

@route.get('/references/slack/thread/{thread_id}/messages')
async def slack_thread_messages(thread_id: str) -> ApiResponse[SlackThreadResponse]: 
    """Retrieve messages for a slack thread by id for the current user."""
    w = Weaviate()
    results = w.get_slack_thread_messages_by_id(thread_id)
    return ApiResponse.create(results) if results else flask.abort(404, f"Thread with id {thread_id} not found")

@route.get('/references/documents')
async def documents() -> ApiResponse[List[DocumentResponse]]:      
    """Retrieve documents for the current user."""
    w = Weaviate()
    return ApiResponse.create(w.get_documents())

@route.get('/references/documents/{document_id}')
async def document(document_id: str) -> ApiResponse[DocumentResponse]:      
    """Retrieve a document by id for the current user."""
    w = Weaviate()
    results = w.get_document_by_id(document_id)
    return ApiResponse.create(results) if results else flask.abort(404, f"Document with id {document_id} not found")

@route.delete('/references/armageddon/{collection}')
async def armaggedon(collection: str) -> str:
    """Truncate a collection in Weaviate."""
    w = Weaviate()
    w.truncate_collection(WeaviateSchemas[collection])
    return f"Collection {collection} truncated"