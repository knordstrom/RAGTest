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
        results = w.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
            filters=Filter.by_property("email_id").equal(email_id),
        )
        if len(results.objects)>0:
            text_results = w.collection(WeaviateSchemas.EMAIL_TEXT).query.fetch_objects(
                filters=Filter.by_property("email_id").equal(email_id),
                sort=Sort.by_property(name="ordinal", ascending=True),
            )
            print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
            response = results.objects[0].properties
            response['text'] = [x.properties.get('text') for x in text_results.objects]

            return response
        else:
            flask.abort(404, f"Email with id {email_id} not found")
    else:
        return [x.properties for x in w.collection(WeaviateSchemas.EMAIL).iterator()]
    
@reference.route('/references/email/thread/<thread_id>', methods=['GET'])
def email_thread(thread_id):
    
    w = Weaviate()
    
    results = w.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
        filters=Filter.by_property("thread_id").equal(thread_id),
    )
    if len(results.objects)>0:
        return [x.properties for x in results.objects]
    else:
        flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/slack/messages/<message_id>', methods=['GET'])
@reference.route('/references/slack/messages', methods=['GET'], defaults={'message_id': None})
def slack_message(message_id) -> str:   
    w = Weaviate()
    
    if message_id:
        results = w.collection(WeaviateSchemas.SLACK_MESSAGE).query.fetch_objects(
            filters=Filter.by_property("message_id").equal(message_id),
        )
        if len(results.objects)>0:
            text_results = w.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).query.fetch_objects(
                filters=Filter.by_property("message_id").equal(message_id),
                sort=Sort.by_property(name="ordinal", ascending=True),
            )
            print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
            response = results.objects[0].properties
            response['text'] = [x.properties.get('text') for x in text_results.objects]
            return response
        else:
            flask.abort(404, f"Message with id {message_id} not found")
    else:
        return [x.properties for x in w.collection(WeaviateSchemas.SLACK_MESSAGE).iterator()]
    
@reference.route('/references/slack/thread/<thread_id>', methods=['GET'])
def slack_thread(thread_id):
  
    w = Weaviate()
    
    results = w.collection(WeaviateSchemas.SLACK_THREAD).query.fetch_objects(
        filters=Filter.by_property("thread_id").equal(thread_id),
    )
    if len(results.objects)>0:
        return [x.properties for x in results.objects]
    else:
        flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/slack/thread/<thread_id>/messages', methods=['GET'])
def slack_thread_messages(thread_id):
  
    w = Weaviate()
    
    results = w.collection(WeaviateSchemas.SLACK_THREAD).query.fetch_objects(
        filters=Filter.by_property("thread_id").equal(thread_id),
    )
    if len(results.objects)>0:
        thread = [x.properties for x in results.objects][0]
        message_results = w.collection(WeaviateSchemas.SLACK_MESSAGE).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
            sort=Sort.by_property(name="ts", ascending=True),
        )
        message_text_results = w.collection(WeaviateSchemas.SLACK_MESSAGE_TEXT).query.fetch_objects(
            filters=Filter.by_property("thread_id").equal(thread_id),
        )

        values = {}
        for text in message_text_results.objects:
            values[text.properties.get('message_id')] = text.properties.get('text')

        for message in message_results.objects:
            message.properties['text'] = values.get(message.properties.get('message_id'))
        
        thread['messages'] = [x.properties for x in message_results.objects]

        return thread
    else:
        flask.abort(404, f"Thread with id {thread_id} not found")



@reference.route('/references/documents/<document_id>', methods=['GET'])
@reference.route('/references/documents', methods=['GET'], defaults={'document_id': None})
def document(document_id):      
        w = Weaviate()
        if document_id:
            results = w.collection(WeaviateSchemas.DOCUMENT).query.fetch_objects(
                filters=Filter.by_property("document_id").equal(document_id),
            )
            if len(results.objects)>0:
                text_results = w.collection(WeaviateSchemas.DOCUMENT_TEXT).query.fetch_objects(
                    filters=Filter.by_property("document_id").equal(document_id),
                    sort=Sort.by_property(name="ordinal", ascending=True),
                )
                summary_results = w.collection(WeaviateSchemas.DOCUMENT_SUMMARY).query.fetch_objects(
                    filters=Filter.by_property("document_id").equal(document_id),
                )

                print("Results", len(results.objects), " with text ", len(text_results.objects), "(",[x.uuid for x in text_results.objects],")")
                response = results.objects[0].properties
                response['text'] = [x.properties.get('text') for x in text_results.objects]
                response['summary'] = [x.properties.get('summary') for x in summary_results.objects][0] if len(summary_results.objects)>0 else {}
                return response
            else:
                flask.abort(404, f"Document with id {document_id} not found")
        else:
            return [x.properties for x in w.collection(WeaviateSchemas.DOCUMENT).iterator()]

@reference.route('/references/armageddon/<collection>', methods=['GET'])
def armaggedon(collection):
    w = Weaviate()
    w.truncate_collection(WeaviateSchemas[collection])
    return f"Collection {collection} truncated"