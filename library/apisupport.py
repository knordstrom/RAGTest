import datetime
import json
import os
import uuid
import flask
from kafka import KafkaProducer
import library.weaviate as weaviate
from library.groq_client import GroqClient
import library.neo4j as neo
from library.gsuite import GSuite, GmailLogic

from groq import Groq
from dotenv import load_dotenv


class APISupport:

    @staticmethod
    def read_last_emails(email: str, creds: str, count = None) -> list[dict]:
        try:
            g: GSuite = GSuite(email, creds)
            gm: GmailLogic = GmailLogic(g)
            ids = gm.get_emails(count)
            mapped = []
            for id in ids:
                mapped.append(gm.get_email(msg_id=id['id']))
            
            return mapped
        finally:
            g.close()

    @staticmethod
    def write_emails_to_kafka(emails: list[dict]) -> None:
        APISupport.write_to_kafka(emails, 'emails',  lambda item: str(item['to'][0]))

    @staticmethod
    def write_slack_to_kafka(slacks: list[dict]) -> None:
        APISupport.write_to_kafka(slacks, 'slack', lambda item: str(item['name']))

    @staticmethod
    def write_cal_to_kafka(events: list[dict]) -> None:
        APISupport.write_to_kafka(events, 'calendar')

    @staticmethod
    def write_docs_to_kafka(doc_info: list[dict]) -> None:
        APISupport.write_to_kafka(doc_info, 'documents')

    @staticmethod
    def write_to_kafka(items: list[dict], channel: str, key_function: callable = lambda x: str(uuid.uuid4())) -> None:
        producer = KafkaProducer(bootstrap_servers=os.getenv('KAFKA_BROKER','127.0.0.1:9092'), 
                                 api_version="7.3.2", 
                                 value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        count = 0
        for item in items:
            if item == None:
                print("Item with no entries found ", item,  "for write to", channel)
                continue
            
            ks = key_function(item)
            key = bytearray().extend(map(ord, ks))
            
            producer.send(channel, key = key, value = item)
            count += 1
        producer.flush()
        print("Wrote ", count, " items to Kafka on channel ", channel)



    # retrieve person node from neo4j
        #    retrieve associated people
        #    retrieve associated events
        # rerieve email chains that are
        #    1. associated with the person
        #    2. pertinent to the event
    @staticmethod
    def create_briefings_for(email: str, start_time: datetime, end_time: datetime) -> dict:
        n = neo.Neo4j()
        n.connect()

        print("Getting schedule for " + email + " from " + start_time.isoformat() + " to " + end_time.isoformat())
        schedule = n.get_schedule(email, start_time, end_time)
        print("Schedule was ", str(schedule))

        prompt = '''### Instruction:
        You are a helpful administrative assistant for the person with the email {email} and you are giving them a briefing
        on what they have to do during the specified time period. In answering the question, please consider the following schedule.

        ### Schedule: {Context}
        ### Question: Given the schedule for {email} from {start_time} to {end_time},
        please describe it succinctly and truthfully. In this description, please point out which attendees will be attending and which have declined the event. 
        A schedule may be empty if there are no events scheduled.
        
        ### Response:
        '''

        context = {
            'email': email,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'Context': str(schedule)
        }

        load_dotenv()

        chat_completion = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=2000).query(prompt, context)

        return {
            "Context": schedule,
            "email": email,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "text": chat_completion
        }
    
    @staticmethod
    def perform_ask(question, key, context_limit = 5, max_tokens=2000):
        vdb = weaviate.Weaviate(os.getenv('VECTOR_DB_HOST',"127.0.0.1"), os.getenv('VECTOR_DB_PORT',"8080"))
        context = vdb.search(question, key, context_limit)
        
        emails = []
        for o in context.objects:
            emails.append(o.properties['text'])
            
        mail_context = '"' + '"\n\n"'.join(emails) + '"\n\n'

        print("Retrieving" + str(len(emails)) + ' emails')
        print("Context " + mail_context)

        # LANGCHAIN IMPLEMENTATION
        prompt='''### Instruction:
        Question: {Question}
        Context: {Context}

        You are a chief of staff for the person asking the question given the Context. 
        Please provide a response to the question in no more than 5 sentences. If the answer is not contained in Context,
        please respond with "I do not know the answer to that question."

        ### Response:'''

        texts = []
        for o in context.objects:
            texts.append(o.properties['text'])

        print(str(texts))
        
        response = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=max_tokens).query(prompt, {'Question':question, 'Context': texts})
        return {
            "Question": question,
            "Response": response,
            "Context": emails,
            
        }

    @staticmethod
    def require(keys: list[str], type = str) -> str:
        for key in keys:
            value = flask.request.args.get(key, type=type)
            if value is not None:         
                return value
        keys = "' or '".join(keys)
        flask.abort(400, f"Missing required parameter '{keys}'")