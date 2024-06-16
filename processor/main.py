import json
from groq import Groq
from kafka import KafkaConsumer, TopicPartition
import os
from library import neo4j
from library.enums.kafka_topics import KafkaTopics
from library.processor_support import ProcessorSupport
import library.weaviate as weaviate
from library.weaviate_schemas import WeaviateSchemas
import library.handlers as h
import traceback
import warnings
from library import neo4j
from datetime import datetime

warnings.simplefilter("ignore", ResourceWarning)

def write_emails_to_vdb(mapped: list) -> None:
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
            print("=> Considering email " + str(j) + " of " + str(len(mapped)) + "...")
            handler.handle_email(email)

            graph_events = []
            for event in events:
                print("Upserting event " + str(event) + " on from " + str(email['from']))     
                event['source'] = 'email'      
                handler.handle_event(event) # , email['from']
                graph_events.append(ProcessorSupport.email_event_to_graph_event(event))
            
            if len(graph_events) > 0:
                write_events_to_neo4j(graph_events)
                    
        print(w.count(WeaviateSchemas.EMAIL))
    finally:
        if w is not None:
            w.close()

def write_events_to_neo4j(events: list):
    graph = neo4j.Neo4j()
    graph.connect()
    graph.process_events(events)

def write_doc_to_vdb(docs):
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