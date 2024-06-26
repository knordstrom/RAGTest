import datetime
import json
import dotenv
import flask

from library.apisupport import APISupport
from library.enums.data_sources import DataSources
from library.gsuite import GSuite
from library.slack import Slack, SlackAuthException
from googleapiclient.errors import HttpError
import os

gsuite_retrieval = flask.Blueprint('gsuite_retrieval', __name__)
require = APISupport.require
dotenv.load_dotenv()

creds = gsuite_retrieval.root_path + '/../' + os.getenv('GSUITE_CREDS_FILE', 'resources/gmail_creds.json')

@gsuite_retrieval.route('/data/gsuite/email', methods=['GET'])
def email() -> str:
    email = require(['email', 'e'])
    count = flask.request.args.get('n', None, int)
    mapped: list = APISupport.read_last_emails(email, creds, count = count)
    APISupport.write_emails_to_kafka(mapped, DataSources.GOOGLE) 
    return mapped

@gsuite_retrieval.route('/data/gsuite/calendar', methods=['GET'])
def calendar() -> str:
    email: str = require(['email', 'e'])
    count = require(['n'], int)

    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print("Getting the upcoming " + str(count) + " events")
        print("Creds " + creds)
        events = GSuite(email, creds).events(now, count)
        APISupport.write_cal_to_kafka(events, DataSources.GOOGLE) 
        return events

    except HttpError as error:
        print(f"An error occurred: {error}")
        flask.abort(400, f"An HTTP error occurred '{error}'")

@gsuite_retrieval.route('/data/gsuite/documents', methods=['GET'])
def documents() -> str:
    email: str = require(['email', 'e'])
    try:
        # now = datetime.datetime.now(datetime.UTC).isoformat()
        print("Getting your documents")
        print("Creds " + creds)
        temp_folder = create_temporary_folder()
        doc_info = GSuite(email, creds, temp_folder).get_doc_info()
        print("doc_info: ", doc_info.keys())
        APISupport.write_docs_to_kafka([x for x in doc_info.values()], DataSources.GOOGLE) 
        return doc_info

    except HttpError as error:
        print(f"An error occurred: {error}")
        flask.abort(400, f"An HTTP error occurred '{error}'")     

def create_temporary_folder():
    root_path = gsuite_retrieval.root_path
    temp_folder = os.path.join(root_path, 'temp', 'gsuite')
    os.makedirs(temp_folder, exist_ok=True)
    return temp_folder