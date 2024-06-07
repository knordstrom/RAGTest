import ast
import json
from library.apisupport import APISupport
from library.slack import Slack, SlackAuthException
import flask

slack_retrieval = flask.Blueprint('slack_retrieval', __name__)
require = APISupport.require


default_destination = {'destination': '/data/slack/channels'}

@slack_retrieval.route('/data/slack/channels', methods=['GET'])
def slack() -> str:
    s = Slack()
    creds = s.check_auth()
    if creds:
        print("Creds valid or expired", creds.valid, creds.expired, creds.expiry)
    if not creds or not creds.valid or creds.expired:
        if creds:
            print("Redirecting to auth", creds.valid, creds.expired, creds.expiry)
        return flask.redirect(s.auth_target(default_destination))
    try:
        conversations = s.read_conversations()
        with open(slack_retrieval.root_path + '/../resources/slack_response.json', 'w') as file:
            json.dump(conversations, file)
        APISupport.write_slack_to_kafka(conversations)
    except SlackAuthException as error:
        return flask.redirect(s.auth_target(default_destination))
    
    return conversations

@slack_retrieval.route('/slack/auth/start', methods=['GET'])
def slack_auth() -> str:
    destination = flask.request.args.get('destination', default_destination['destination'])
    s = Slack()
    creds = s.check_auth()
    if not creds or not creds.valid:
        return flask.redirect(s.auth_target({'destination': destination}))
    else:
        return flask.redirect(destination)
    

@slack_retrieval.route("/slack/auth/finish", methods=["GET", "POST"])
def slack_auth_finish():
    # Retrieve the auth code and state from the request params
    auth_code = require(["code"])
    received_state = ast.literal_eval(flask.request.args.get("state",str(default_destination)))
    s = Slack()
    result = s.finish_auth(auth_code)
    return flask.redirect(received_state.get('destination', default_destination['destination']))