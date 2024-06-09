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
def email(email_id) -> str:
    
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
def thread(thread_id):
    
    w = Weaviate()
    
    results = w.collection(WeaviateSchemas.EMAIL).query.fetch_objects(
        filters=Filter.by_property("thread_id").equal(thread_id),
    )
    if len(results.objects)>0:
        return [x.properties for x in results.objects]
    else:
        flask.abort(404, f"Thread with id {thread_id} not found")

@reference.route('/references/armageddon/<collection>', methods=['GET'])
def armaggedon(collection):
    w = Weaviate()
    w.truncate_collection(WeaviateSchemas[collection])
    return f"Collection {collection} truncated"