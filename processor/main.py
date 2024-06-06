import json
from kafka import KafkaConsumer, TopicPartition
import os
from library import neo4j
import library.weaviate as weaviate
import library.handlers as h
import library.handlers as h
import traceback
import warnings
from library import neo4j
from datetime import datetime
from groq import Groq

warnings.simplefilter("ignore", ResourceWarning)

def write_to_vdb(mapped: list) -> None:
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

            for event in events:
                print("Upserting event " + str(event) + " on from " + str(email['from']))
                handler.handle_event(event) # , email['from']
                    
        print(w.count(weaviate.WeaviateSchemas.EMAIL))
    finally:
        if w is not None:
            w.close()

def write_to_neo4j(events):
    graph = neo4j.Neo4j()
    graph.connect()
    graph.process_events(events)

def write_doc_to_vdb(docs):
    db = "docker-weaviate-1"
    db_port = "8080"
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



def kafka_listen(default_topic: str, group: str, endpoint: callable):
    kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
    topic = os.getenv("KAFKA_TOPIC", default_topic)
    print("Starting processor at " + kafka + " on topic " + topic + " ...")
    try:
        consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                group_id=group,
                                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                                max_poll_records=10,
                                api_version="7.3.2")
        consumer.subscribe(topics=[topic])
        print("Subscribed to " + topic + ", waiting for messages...")
        count = 0

        key: TopicPartition = TopicPartition(topic=topic, partition=0)
        partitions = None
        message = None
        while partitions == None or len(partitions) == 0:
            partitions = consumer.partitions_for_topic(topic)
            print("Waiting for partitions... have " + str(partitions))
        
        while True:
            print("Tick")
            try:
                message = consumer.poll(timeout_ms=2000)
            except Exception as e:
                print("Error: " + str(e))
                continue

            if message is None or message == {}:  
                continue
            else:
                count += 1
                print("Received message " + str(count) + ":" + str(message))
                print()

                endpoint(message[key])
                print(" ... written to VDB")
            
            consumer.commit()

    finally:
        print("Closing consumer")
        consumer.close()

def start():
    kafka_listen("emails", "email_processor", write_to_vdb)

def start_kafka_calendar():
    kafka_listen("calendar", "calendar_processor", write_to_neo4j)

def start_kafka_documents():
    kafka_listen("documents", "document_processor", write_doc_to_vdb)

if __name__ == '__main__':
    start()