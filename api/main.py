import datetime
from dateutil import parser as dateparser

from os import abort
import flask
from library.apisupport import APISupport
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
    query = require(['query', 'q'])
    count = flask.request.args.get('n', None, int)
    return APISupport.perform_ask(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)

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

if __name__ == '__main__':
    app.run()