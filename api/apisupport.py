from datetime import date
import datetime
import json
from kafka import KafkaProducer
from library.llm_api import LLM_API
import library.neo4j as neo
from library.gmail import Gmail, GmailLogic
from library import weaviate as we  


class APISupport:

    @staticmethod
    def read_last_emails(email: str, creds: str, count = None) -> list[dict]:
        try:
            g: Gmail = Gmail(email, creds)
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

    # retrieve person node from neo4j
        #    retrieve associated people
        #    retrieve associated events
        # rerieve email chains that are
        #    1. associated with the person
        #    2. pertinent to the event
    @staticmethod
    def create_briefings_for(email: str, start_time: datetime, end_time: datetime) -> dict:
        n = neo.Neo4j()

        print("Getting schedule for " + email + " from " + start_time.isoformat() + " to " + end_time.isoformat())
        schedule = n.get_schedule(email, start_time, end_time)
        print("Schedule was ", str(schedule))

        llm = LLM_API('localhost', '4891', we.Weaviate())

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

        
        response = llm.query_with_template(prompt, context, context_limit = 3)

        return response
    
