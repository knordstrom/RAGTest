from datetime import datetime
from groq import Groq
from kafka import TopicPartition
import os
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

def write_doc_to_vdb(docs: list[ConsumerRecord]):
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

def start_kafka_documents():
    ProcessorSupport.kafka_listen(KafkaTopics.DOCUMENTS, "document_processor", write_doc_to_vdb)

if __name__ == '__main__':
    start_kafka_documents()