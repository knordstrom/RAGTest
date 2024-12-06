from datetime import datetime
import threading
from fastapi import FastAPI
from groq import Groq
from kafka import TopicPartition
import os

import uvicorn
from api import metrics
from library.data.local import neo4j
from library.models.api_models import MeetingAttendee
from library.enums.kafka_topics import KafkaTopics
from library.managers.processor_support import ProcessorSupport
import library.data.local.weaviate as weaviate
from library.models.weaviate_schemas import Event, WeaviateSchemas
import library.models.event as event
import library.managers.handlers as h
import warnings
from library.data.local import neo4j
from kafka.consumer.fetcher import ConsumerRecord

warnings.simplefilter("ignore", ResourceWarning)

def write_emails_to_vdb(mapped: list[ConsumerRecord]) -> None:
    db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
    db_port = os.getenv("VECTOR_DB_PORT", "8080")
    print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(mapped)))
    w = None
    try:
        w = weaviate.Weaviate(db, db_port)
        handler = h.Handlers(w)
        for j,record in enumerate(mapped):
            email: dict = record.value
            events = email.get('events', [])
            email.pop('events', None)
            print("=> Considering email ",j," of ",len(mapped),"...")
            handler.handle_email(email)

            graph_events = []
            for event in events:
                event['source'] = 'email'      
                print("Upserting event ", event, " on from ", email['sender'])
                print("Email was", email)     

                event_obj = Event(
                    event_id=event['event_id'], 
                    summary=event['summary'], 
                    location=event.get('location'), 
                    start=datetime.fromisoformat(event['start']), 
                    end=datetime.fromisoformat(event['end']), 
                    email_id=email['email_id'], 
                    sent_date=datetime.fromisoformat(email['date']), 
                    sender=event['organizer']['email'],
                    to=email['to'][0]['email'], 
                    thread_id=email['thread_id'], 
                    name=email['subject'], 
                    description=event['description'], 
                    provider=email['provider']
                )

                attendees = [MeetingAttendee(email=attendee['email'], name=attendee['name']) for attendee in event['attendees']]

                handler.handle_event(event_obj)
                graph_events.append(ProcessorSupport.email_event_to_graph_event(event_obj, attendees))
            
            if len(graph_events) > 0:
                write_events_to_neo4j(graph_events)
                    
        print(w.count(WeaviateSchemas.EMAIL))
    finally:
        if w is not None:
            w.close()

def write_events_to_neo4j(events: list[ConsumerRecord]) -> None:
    graph = neo4j.Neo4j()
    graph.process_events(events)

def listen_to_kafka():
    ProcessorSupport.kafka_listen(KafkaTopics.EMAILS, "email_processor", write_emails_to_vdb)   

def serve_metrics():
    app = FastAPI(title="Email Processor", version="0.1")
    metrics_app = metrics.MetricsApp(app, prefix="email_processor", use_kafka=True, use_neo4j=True, use_weaviate=True).make_metrics_app()
    print("Metrics server starting at", metrics_app)

    uvicorn.run(app, host="0.0.0.0", port=5011)
    
def start():
    print("Starting email processor...")
    thread = threading.Thread(target = listen_to_kafka)
    thread.daemon = False
    thread.start()

    serve_metrics()
    
    print("Email processor started")

if __name__ == '__main__':
    start()