import datetime
import json
import os
import uuid
from fastapi import HTTPException
from kafka import KafkaProducer
from library.models.api_models import AskRequestContext, AskResponse, Meeting, ScheduleResponse
from library.enums.data_sources import DataSources
from library.enums.kafka_topics import KafkaTopics
from library.enums.kafka_topics import KafkaTopics
from library.models.employee import User
from library.models.event import Event
from library.models.message import Message
from library.llms.promptmanager import PromptManager
import library.data.local.weaviate as weaviate
from library.llms.groq_client import GroqClient
import library.data.local.neo4j as neo
from library.data.external.gsuite import GSuite, GmailLogic
from weaviate.collections.classes.internal import Object
from library.models.api_models import ConferenceCall

from groq import Groq
from dotenv import load_dotenv

class APISupport:

    @staticmethod
    def read_last_emails(user: User, creds: str, count = None) -> list[Message]:
        try:
            g: GSuite = GSuite(user, creds)
            gm: GmailLogic = GmailLogic(g)
            ids: list[dict[str, str]] = gm.get_emails(count)
            mapped: list[Message] = []
            for id in ids:
                mapped.append(gm.get_email(msg_id=id['id']))
            
            return mapped
        finally:
            g.close()

    @staticmethod
    def write_emails_to_kafka(emails: list[Message], provider: DataSources, person: User) -> None:
        written = []
        for email in emails:
            to_add = email.model_dump()
            to_add['provider'] = provider.value
            to_add['person_id'] = person.id
            written.append(to_add)
        APISupport.write_to_kafka(written, KafkaTopics.EMAILS, provider,  lambda item: str(item['to'][0]))

    @staticmethod
    def write_slack_to_kafka(slacks: list[dict[str, any]]) -> None:
        APISupport.write_to_kafka(slacks, KafkaTopics.SLACK, DataSources.SLACK, lambda item: str(item['name']))

    @staticmethod
    def write_cal_to_kafka(events: list[dict[str, any]], provider: DataSources) -> None:
        APISupport.write_to_kafka(events, KafkaTopics.CALENDAR, provider)

    @staticmethod
    def write_docs_to_kafka(docs: list[dict[str, any]], provider: DataSources) -> None:  
        APISupport.write_to_kafka(docs, KafkaTopics.DOCUMENTS,  provider)

    @staticmethod
    def write_conferences_to_kafka(conferences: list[ConferenceCall], provider: DataSources) -> None:
        written = [conference.model_dump() for conference in conferences]
        APISupport.write_to_kafka(written, KafkaTopics.CONFERENCES, provider)

    @staticmethod
    def write_transcripts_to_kafka(transcripts: dict[str,any], provider: DataSources) -> None:
        written = [transcript for transcript in transcripts.values()]
        APISupport.write_to_kafka(written, KafkaTopics.TRANSCRIPTS, provider)

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
    def perform_ask(user: User, question: str, key: str, context_limit: int = 5, max_tokens: int = 2000, 
                    certainty: float = None, threshold: float = None, use_hyde: bool = False) -> AskResponse:
        vdb: weaviate.Weaviate = weaviate.Weaviate(os.getenv('VECTOR_DB_HOST',"127.0.0.1"), os.getenv('VECTOR_DB_PORT',"8080"))
        context: list[Object] = vdb.search(user, question, key, context_limit, certainty = certainty,threshold = threshold, use_hyde = use_hyde)
        
        emails = []
        for o in context:
            emails.append(o.properties['text'])
            
        mail_context = '"' + '"\n\n"'.join(emails) + '"\n\n'

        print("Retrieving" + str(len(emails)) + ' emails')
        print("Context " + mail_context)

        # LANGCHAIN IMPLEMENTATION
        pm: PromptManager = PromptManager()
        prompt:str = pm.get_latest_prompt_template('APISupport.perform_ask')

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
    def error_response(code: int, message: str) -> None:
        raise HTTPException(status_code=code, detail=message)
    
    @staticmethod
    def assert_not_none(value: any, message: str) -> None:
        if value is None:
            APISupport.error_response(404, message)