import datetime
import json
import flask

from library.apisupport import APISupport
from library.gsuite import GSuite
from library.slack import Slack, SlackAuthException
from googleapiclient.errors import HttpError

from library.weaviate import Weaviate
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from weaviate.classes.query import Filter
from weaviate.collections.classes.grpc import Sort

reference = flask.Blueprint('reference', __name__)
require = APISupport.require

@reference.route('/references/email/messages/<email_id>', methods=['GET'])
@reference.route('/references/email/messages', methods=['GET'], defaults={'email_id': None})
def email_message(email_id) -> str:  
    w = Weaviate()  
    if email_id:
        response = w.get_email_by_id(email_id)
        return response if response else flask.abort(404, f"Email with id {email_id} not found")
    else:
        return w.get_emails()
    
@reference.route('/references/email/thread/<thread_id>', methods=['GET'])
def email_thread(thread_id): 
    w = Weaviate()   
    result = w.get_thread_by_id(thread_id)
    return result if result else flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/slack/messages/<message_id>', methods=['GET'])
@reference.route('/references/slack/messages', methods=['GET'], defaults={'message_id': None})
def slack_message(message_id) -> str:   
    w = Weaviate()
    if message_id:
        results = w.get_slack_message_by_id(message_id)
        return results if results else flask.abort(404, f"Message with id {message_id} not found")
    else:
        return w.get_slack_messages()
    
@reference.route('/references/slack/thread/<thread_id>', methods=['GET'])
def slack_thread(thread_id):
    w = Weaviate()   
    result = w.get_slack_thread_by_id(thread_id)
    return result if result else flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/slack/thread/<thread_id>/messages', methods=['GET'])
def slack_thread_messages(thread_id): 
    w = Weaviate()
    results = w.get_slack_thread_messages_by_id(thread_id)
    return results if results else flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/documents/<document_id>', methods=['GET'])
@reference.route('/references/documents', methods=['GET'], defaults={'document_id': None})
def document(document_id):      
    w = Weaviate()
    if document_id:
        results = w.get_document_by_id(document_id)
        return results if results else flask.abort(404, f"Document with id {document_id} not found")
    else:
        return w.get_documents()

@reference.route('/references/armageddon/<collection>', methods=['GET'])
def armaggedon(collection):
    w = Weaviate()
    w.truncate_collection(WeaviateSchemas[collection])
    return f"Collection {collection} truncated"