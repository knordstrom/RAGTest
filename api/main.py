import datetime
import os
from dateutil import parser as dateparser

from os import abort
import flask
from library.apisupport import APISupport
from googleapiclient.errors import HttpError
import context
from library.gmail import Gmail
import library.weaviate as weaviate
import warnings

warnings.simplefilter("ignore", ResourceWarning)

app = flask.Flask(__name__)

@app.route('/ask', methods=['GET'])
def ask() -> str:
    query = require(['query', 'q'])
    count = flask.request.args.get('n', None, int)
    return APISupport.perform_ask(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)


@app.route('/email', methods=['GET'])
def email() -> str:
    email = require(['email', 'e'])
    count = flask.request.args.get('n', None, int)
    mapped: list = APISupport.read_last_emails(email, app.root_path + '/../resources/gmail_creds.json', count = count)
    APISupport.write_to_kafka(mapped)
    return mapped


@app.route('/briefs', methods=['GET'])
def briefs() -> str:
    email: str = require(['email', 'e'])
    print("Email", email)
    start_time: datetime = to_date_time(require(['start']), 'start')
    print("Start time", start_time, type(start_time))
    plus12 = start_time + datetime.timedelta(hours=12)
    print("Start time plus12", plus12, type(plus12))
    end_time: datetime = to_date_time(flask.request.args.get('end',default = plus12.isoformat()), 'end')
    return APISupport.create_briefings_for(email, start_time, end_time)

@app.route('/calendar', methods=['GET'])
def calendar() -> str:
    email: str = require(['email', 'e'])
    count = require(['n'], int)

    try:
        now = datetime.datetime.now(datetime.UTC).isoformat()
        print("Getting the upcoming " + str(count) + " events")
        print("Creds " + app.root_path + '/../resources/gmail_creds.json')
        events = Gmail(email, app.root_path + '/../resources/gmail_creds.json').events(now, count)
        APISupport.write_to_kafka_cal(events)
        return events

    except HttpError as error:
        print(f"An error occurred: {error}")
        flask.abort(400, f"An HTTP error occurred '{error}'")


def to_date_time(date: str, name: str) -> datetime:
    try:
       return dateparser.parse(date)
    except ValueError:
        flask.abort(400, "Invalid time value for parameter " + name + ". Please express the value in ISO 8601 format." )

def require(keys: list[str], type = str) -> str:
    for key in keys:
        value = flask.request.args.get(key, type=type)
        if value is not None:         
            return value
    keys = "' or '".join(keys)
    flask.abort(400, f"Missing required parameter '{keys}'")



if __name__ == '__main__':
    app.run()