import json
from os import abort
import flask
import context
from library.gmail import Gmail, GmailLogic
from library.llm import LLM, Wizard, Hermes, Falcon, Mini, MistralInstruct, MistralOrca
import importlib as i
import library.weaviate as weaviate
from kafka import KafkaProducer

class APISupport:

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
    def get_list_from_string(self, string: str) -> list:
        if string == None:
            return []
        return list(map(int, string.split(',')))

app = flask.Flask(__name__)

@app.route('/ask', methods=['GET'])
def ask() -> str:
    query = flask.request.args.get('q')
    count = flask.request.args.get('n', None, int)
    if query is not None and query != '':
        w: LLM = MistralInstruct(weaviate.Weaviate("http://127.0.0.1:8080"))
        return w.query(query, weaviate.WeaviateSchemas.EMAIL_TEXT, context_limit = count)
    else:
        flask.abort(404)
        return "No query provided"

@app.route('/email', methods=['GET'])
def email() -> str:
    email = flask.request.args.get('e')
    count = flask.request.args.get('n', None, int)

    if email is not None and email != '':
        mapped: list = APISupport.read_last_emails(email, count = count)
        APISupport.write_to_kafka(mapped)
        return mapped
    else:
        flask.abort(404)
        return "No email provided"

if __name__ == '__main__':
    app.run()