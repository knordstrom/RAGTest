from datetime import datetime
from groq import Groq
from kafka import TopicPartition
import os
from library import neo4j
from library.api_models import MeetingAttendee
from library.enums.kafka_topics import KafkaTopics
from library.processor_support import ProcessorSupport
import library.weaviate as weaviate
from library.weaviate_schemas import Event, WeaviateSchemas
import library.models.event as event
import library.handlers as h
import warnings
from library import neo4j

warnings.simplefilter("ignore", ResourceWarning)

def write_emails_to_vdb(mapped: list[dict[str, any]]) -> None:
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

def write_events_to_neo4j(events: list[event.Event]) -> None:
    graph = neo4j.Neo4j()
    graph.process_events(events)

def write_doc_to_vdb(docs: list[dict[str, any]]):
    db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
    db_port = os.getenv("VECTOR_DB_PORT", "8080")
    print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(docs)))
    w = None
    try:
        g = Groq(api_key=os.getenv("GROQ_API_KEY"))
        w = weaviate.Weaviate(db, db_port)
        handler = h.Handlers(w, g)
        print("number of received documents: ", len(docs))
        for doc in docs:
            handler.handle_document(doc.value)
            doc_id = doc.value.get("document_id")
            doc_type = doc.value.get("doc_type")
            print(f"document added {doc_id} of type {doc_type}")
        count_doc_summary = w.count(weaviate.WeaviateSchemas.DOCUMENT_SUMMARY)
        count_doc = w.count(weaviate.WeaviateSchemas.DOCUMENT)
        count_doc_text = w.count(weaviate.WeaviateSchemas.DOCUMENT_TEXT)   
        print(f"number of entries in document summary: {count_doc_summary}")
        print(f"number of entries in document: {count_doc}")
        print(f"number of entries in document text: {count_doc_text}")
    finally:
        if w is not None:
            w.close()

def start():
    ProcessorSupport.kafka_listen(KafkaTopics.EMAILS, "email_processor", write_emails_to_vdb)

def start_kafka_calendar():
    ProcessorSupport.kafka_listen(KafkaTopics.CALENDAR, "calendar_processor", write_events_to_neo4j)

def start_kafka_documents():
    ProcessorSupport.kafka_listen(KafkaTopics.DOCUMENTS, "document_processor", write_doc_to_vdb)

if __name__ == '__main__':
    start()