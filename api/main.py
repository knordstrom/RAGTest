import ast
import datetime
from dateutil import parser as dateparser

from os import abort
import dotenv
import flask
from library.apisupport import APISupport
from library.briefing_support import BriefingSupport
import library.weaviate as weaviate
import warnings 

from api.gsuite_retrieval import gsuite_retrieval
from slack_retrieval import slack_retrieval
from reference import reference

warnings.simplefilter("ignore", ResourceWarning)

app = flask.Flask(__name__)
app.register_blueprint(gsuite_retrieval)
app.register_blueprint(slack_retrieval)
app.register_blueprint(reference)

require = APISupport.require

@app.route('/ask', methods=['GET'])
def ask() -> str:
    """Ask Weaviate a question. Will leverage [email] for context."""
    query = require(['query', 'q'])
    count = flask.request.args.get('n', None, int)
    return APISupport.perform_ask(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)

@app.route('/briefs', methods=['GET'])
def briefs() -> str:
    """Create briefings for a user."""
    certainty = flask.request.args.get('certainty', None, float)
    if certainty is not None:
        if certainty < 0 or certainty > 100:
            flask.abort(400, "Confidence must be a percentage value between 0 and 100.")
        else:
            certainty = certainty / 100
    email: str = require(['email', 'e'])
    start_time: datetime = to_date_time(require(['start']), 'start')
    plus12 = start_time + datetime.timedelta(hours=12)
    end_time: datetime = to_date_time(flask.request.args.get('end',default = plus12.isoformat()), 'end')
    return BriefingSupport.create_briefings_for(email, start_time, end_time, certainty = certainty)

@app.route('/schedule', methods=['GET'])
def schedule() -> str:
    """Retrieves the schedule for a user."""
    email: str = require(['email', 'e'])
    start_time: datetime = to_date_time(require(['start']), 'start')
    end_time: datetime = to_date_time(require(['end']), 'end')
    return APISupport.get_calendar_between(email, start_time, end_time)

def to_date_time(date: str, name: str) -> datetime:
    try:
       return dateparser.parse(date)
    except ValueError:
        flask.abort(400, "Invalid time value for parameter " + name + ". Please express the value in ISO 8601 format." )

if __name__ == '__main__':
    app.run()