import datetime
from dateutil import parser as dateparser
import json
from os import abort
import flask
from api.apisupport import APISupport
# import context
from library.gmail import Gmail, GmailLogic
from library.llm import LLM, Wizard, Hermes, Falcon, Mini, MistralInstruct, MistralOrca
import importlib as i
import library.weaviate as weaviate
from kafka import KafkaProducer
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import warnings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

class APISupport:

    @staticmethod
    def read_last_emails(email: str, count = None) -> list[dict]:
        try:
            g: Gmail = Gmail(email, app.root_path + '/../resources/gmail_creds.json')
            gm: GmailLogic = GmailLogic(g)
            ids = gm.get_emails(count)
            mapped = []
            for id in ids:
                mapped.append(gm.get_email(msg_id=id['id']))
            
            return mapped
        finally:
            g.close()

    @staticmethod
    def write_to_kafka(emails: list[dict]) -> None:
        producer = KafkaProducer(bootstrap_servers='127.0.0.1:9092', 
                                 api_version="7.3.2", 
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        count = 0
        for email in emails:
            if email == None:
                print("Email with no entries found " + str(email) + "...")
                continue
            
            ks = str(email['to'][0])
            key = bytearray().extend(map(ord, ks))
            
            producer.send('emails', key = key, value = email)
            count += 1
        producer.flush()
        print("Wrote " + str(count) + " emails to Kafka")

    @staticmethod
    def write_to_kafka_cal(events: dict) -> None:
        producer = KafkaProducer(bootstrap_servers='127.0.0.1:9092', 
                                 api_version="7.3.2", 
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        count = 0
        # for person in people:
        #     if person == None:
        #         print("There are no attendees")
        #         continue
        #     producer.send('calendar', value = person)
        
        for event in events:
            count += 1
            if event == None:
                print("There are no events")
                continue
            producer.send('calendar', value = event)

        # for attendance in attendances:
        #     if attendance == None:
        #         print("There are no relationships")
        #         continue
        #     producer.send('calendar', value = attendance)
        producer.flush()
        print("Wrote " + str(count) + " calendar events to Kafka")

    @staticmethod
    def get_list_from_string(self, string: str) -> list:
        if string == None:
            return []
        return list(map(int, string.split(',')))

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


@app.route('/calendar', methods=['GET'])
def calendar() -> str:
    count = flask.request.args.get('n', None, int)
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../resources/gmail_creds.json", SCOPES
            )
            creds = flow.run_local_server(port=3000)
            # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=count,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        print("events: ", events)
        if not events:
            print("No upcoming events found.")
            return
        APISupport.write_to_kafka_cal(events)
        return events
            

    except HttpError as error:
        print(f"An error occurred: {error}")
        return "error"
            

    except HttpError as error:
        print(f"An error occurred: {error}")
        return "error"
       
if __name__ == '__main__':
    app.run()