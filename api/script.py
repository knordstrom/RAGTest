import json
import os
from typing import List

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os
from typing import Union

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import json
from library.apisupport import APISupport
from library.slack import Slack, SlackAuthException
from library.enums.data_sources import DataSources
from googleapiclient.errors import HttpError
from library.models.message import Message
from pydantic import TypeAdapter

route = APIRouter(tags=["Data Acquisition"])

root_path = os.path.dirname(os.path.realpath(__file__))

default_destination = {'destination': '/data/script'}

@route.get('/data/script')
def slack() -> str:
    """This script is used to ingest demo information from a script to automate data ingestion"""
    try:
        with open(root_path + '/../demo_script/calendar.json', 'r') as cal_file:
            cal_data = json.load(cal_file)
        APISupport.write_cal_to_kafka(cal_data, DataSources.GOOGLE)
        with open(root_path + '/../demo_script/email.json', 'r') as email_file:
            email_data = json.load(email_file)
        adapter = TypeAdapter(List[Message])
        emails = adapter.validate_python(email_data)
        APISupport.write_emails_to_kafka(emails, DataSources.GOOGLE)
        with open(root_path + '/../demo_script/documents.json', 'r') as docs_file:
            docs_data = json.load(docs_file)
        APISupport.write_docs_to_kafka([x for x in docs_data.values()], DataSources.GOOGLE)

        # TODO: Uncomment the below code when the script is ready
        # s = Slack()
        # conversations = s.read_conversations()
        with open(root_path + '/../demo_script/slack.json', 'r') as slack_file:
            conversations = json.load(slack_file)
        APISupport.write_slack_to_kafka(conversations)
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        APISupport.error_response(400, f"An HTTP error occurred '{error}'")
    return "successfully ingested!"

