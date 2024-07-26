import ast
import json
import os
from typing import Union

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import os
from typing import Union

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from library.apisupport import APISupport
from library.slack import Slack, SlackAuthException

route = APIRouter(tags=["Data Acquisition"])

root_path = os.path.dirname(os.path.realpath(__file__))

default_destination = {'destination': '/data/slack/channels'}

@route.get('/data/slack/channels')
def slack() -> str:
    """Retrieve slack channels for the current user. THIS CURRENTLY DOES NOT WORK WITHOUT MANUAL INCLUSION OF SLACK CREDENTIALS."""
    s = Slack()
    creds = s.check_auth()
    if creds:
        print("Creds valid or expired", creds.valid, creds.expired, creds.expiry)
    if not creds or not creds.valid or creds.expired:
        if creds:
            print("Redirecting to auth", creds.valid, creds.expired, creds.expiry)
        return RedirectResponse(url=s.auth_target(default_destination))
    try:
        conversations = s.read_conversations()
        with open(root_path + '/../resources/slack_response.json', 'w') as file:
            json.dump(conversations, file)
        APISupport.write_slack_to_kafka(conversations)
    except SlackAuthException as error:
        return RedirectResponse(url=s.auth_target(default_destination))
    return conversations

@route.get('/slack/auth/start', include_in_schema=False)
def slack_auth(destination: Union[str,None] = None) -> str:
    destination = destination if destination else default_destination['destination']
    s = Slack()
    creds = s.check_auth()
    if not creds or not creds.valid:
        return RedirectResponse(url=s.auth_target({'destination': destination}))
    else:
        return RedirectResponse(url=destination)


@route.get("/slack/auth/finish", include_in_schema=False)
def slack_auth_finish(code:str, state:Union[str,None] = None):
    # Retrieve the auth code and state from the request params

    received_state = ast.literal_eval(state if state else str(default_destination))
    s = Slack()
    result = s.finish_auth(code)
    return RedirectResponse(url=received_state.get('destination', default_destination['destination']))
