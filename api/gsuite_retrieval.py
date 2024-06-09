import datetime
import json
import flask

from library.apisupport import APISupport
from library.gsuite import GSuite
from library.slack import Slack, SlackAuthException
from googleapiclient.errors import HttpError

gsuite_retrieval = flask.Blueprint('gsuite_retrieval', __name__)
require = APISupport.require

@gsuite_retrieval.route('/data/gsuite/email', methods=['GET'])
def email() -> str:
    email = require(['email', 'e'])
    count = flask.request.args.get('n', None, int)
    mapped: list = APISupport.read_last_emails(email, gsuite_retrieval.root_path + '/../resources/gmail_creds.json', count = count)
    APISupport.write_emails_to_kafka(mapped)
    return mapped

@gsuite_retrieval.route('/data/gsuite/calendar', methods=['GET'])
def calendar() -> str:
    email: str = require(['email', 'e'])
    count = require(['n'], int)

    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print("Getting the upcoming " + str(count) + " events")
        print("Creds " + gsuite_retrieval.root_path + '/../resources/gmail_creds.json')
        events = GSuite(email, gsuite_retrieval.root_path + '/../resources/gmail_creds.json').events(now, count)
        APISupport.write_cal_to_kafka(events)
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
        print("Creds " + gsuite_retrieval.root_path + '/../resources/gmail_creds.json')
        doc_info = GSuite(email, gsuite_retrieval.root_path + '/../resources/gmail_creds.json').get_doc_info()
        print("doc_info: ", doc_info)
        APISupport.write_docs_to_kafka(doc_info)
        return doc_info

    except HttpError as error:
        print(f"An error occurred: {error}")
        flask.abort(400, f"An HTTP error occurred '{error}'")        