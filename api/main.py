import datetime
from dateutil import parser as dateparser
import json
from os import abort
import flask
from api.apisupport import APISupport
import context
from library.gmail import Gmail, GmailLogic
from library.llm import LLM, Wizard, Hermes, Falcon, Mini, MistralInstruct, MistralOrca
import importlib as i
import library.weaviate as weaviate
from kafka import KafkaProducer
import warnings

warnings.simplefilter("ignore", ResourceWarning)

app = flask.Flask(__name__)

@app.route('/ask', methods=['GET'])
def ask() -> str:
    query = email = require(['query', 'q'])
    count = flask.request.args.get('n', None, int)

    w: LLM = MistralInstruct(weaviate.Weaviate("127.0.0.1", "8080"))
    return w.query(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)


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