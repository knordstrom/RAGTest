import datetime
import json
import os
import uuid
from fastapi import HTTPException
from kafka import KafkaProducer
from library.api_models import AskRequestContext, AskResponse, Meeting, ScheduleResponse
from library.enums.data_sources import DataSources
from library.enums.kafka_topics import KafkaTopics
from library.enums.kafka_topics import KafkaTopics
from library.models.event import Event
from library.models.message import Message
import library.weaviate as weaviate
from library.groq_client import GroqClient
import library.neo4j as neo
from library.gsuite import GSuite, GmailLogic
from weaviate.collections.classes.internal import Object

from groq import Groq
from dotenv import load_dotenv

class APISupport:

    @staticmethod
    def read_last_emails(email: str, creds: str, count = None) -> list[Message]:
        try:
            g: GSuite = GSuite(email, creds)
            gm: GmailLogic = GmailLogic(g)
            ids: list[dict[str, str]] = gm.get_emails(count)
            mapped: list[Message] = []
            for id in ids:
                mapped.append(gm.get_email(msg_id=id['id']))
            
            return mapped
        finally:
            g.close()

    @staticmethod
    def write_emails_to_kafka(emails: list[Message], provider: DataSources) -> None:
        written = [email.model_dump() for email in emails]
        APISupport.write_to_kafka(written, KafkaTopics.EMAILS, provider,  lambda item: str(item['to'][0]))

    @staticmethod
    def write_slack_to_kafka(slacks: list[dict]) -> None:
        APISupport.write_to_kafka(slacks, KafkaTopics.SLACK, DataSources.SLACK, lambda item: str(item['name']))

    @staticmethod
    def write_cal_to_kafka(events: list[dict], provider: DataSources) -> None:
        APISupport.write_to_kafka(events, KafkaTopics.CALENDAR, provider)

    @staticmethod
    def write_docs_to_kafka(docs: list[dict], provider: DataSources) -> None:  
        APISupport.write_to_kafka(docs, KafkaTopics.DOCUMENTS,  provider)


    def handle_json(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError("Type not serializable  " + str(obj))

    @staticmethod
    def write_to_kafka(items: list[dict], topic_channel: KafkaTopics, provider: DataSources, key_function: callable = lambda x: str(uuid.uuid4())) -> None:
        channel = topic_channel.value
        producer = KafkaProducer(bootstrap_servers=os.getenv('KAFKA_BROKER','127.0.0.1:9092'), 
                                 api_version="7.3.2", 
                                 value_serializer=lambda v: json.dumps(v, default=APISupport.handle_json).encode('utf-8'))
        count = 0
        for item in items:
            # item['provider'] = provider.value
            if item == None:
                print("Item with no entries found ", item,  "for write to", channel)
                continue
            item['provider'] = provider.value
            ks = key_function(item)
            key = bytearray().extend(map(ord, ks))
            
            producer.send(channel, key = key, value = item)
            count += 1
        producer.flush()
        print("Wrote ", count, " items to Kafka on channel ", channel)    
    
    @staticmethod
    def perform_ask(question: str, key: str, context_limit: int = 5, max_tokens: int =2000) -> AskResponse:
        vdb: weaviate.Weaviate = weaviate.Weaviate(os.getenv('VECTOR_DB_HOST',"127.0.0.1"), os.getenv('VECTOR_DB_PORT',"8080"))
        context: list[Object] = vdb.search(question, key, context_limit)
        
        emails = []
        for o in context:
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
        for o in context:
            texts.append(o.properties['text'])

        print(str(texts))
        
        response = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=max_tokens).query(prompt, {'Question':question, 'Context': texts})
        return AskResponse(
            question = question,
            response = response,
            context = AskRequestContext(emails = emails)        
        )
    
    @staticmethod
    def get_calendar_between(email: str, start_time: datetime, end_time: datetime) -> ScheduleResponse:
        n = neo.Neo4j()
        print("Getting calendar for " + email + " from " + start_time.isoformat() + " to " + end_time.isoformat())
        events: list[Event] = n.get_schedule(email, start_time, end_time)

        meetings: list[Meeting] = []
        for event in events:
            m = event.model_dump()
            m['name'] = m.get('summary', 'No Title')
            meetings.append(Meeting(**m))

        return ScheduleResponse(
            email  = email,
            start_time = start_time.isoformat(),
            end_time = end_time.isoformat(),
            events = meetings
        )

    @staticmethod
    def error_response(code: int, message: str) -> dict:
        raise HTTPException(status_code=code, detail=message)