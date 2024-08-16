from datetime import datetime
import dotenv
from groq import Groq
from kafka import TopicPartition
import os
from library import neo4j
from library.api_models import ConferenceTranscript, MeetingAttendee, TranscriptConversation, TranscriptLine
from library.enums.kafka_topics import KafkaTopics
from library.processor_support import ProcessorSupport
import library.weaviate as weaviate
from library.weaviate_schemas import Event, WeaviateSchemas
import library.models.event as event
import library.handlers as h
import warnings
from library import neo4j

warnings.simplefilter("ignore", ResourceWarning)   

def write_transcripts_to_vdb(docs: list[dict[str, any]]):
    db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
    db_port = os.getenv("VECTOR_DB_PORT", "8080")
    print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(docs)))
    w: weaviate.Weaviate = None
    print("Received documents: ", docs)
    try:
        g = Groq(api_key=os.getenv("GROQ_API_KEY"))
        w = weaviate.Weaviate(db, db_port)
        handler: h.Handlers = h.Handlers(w, g)
        # print("number of received documents: ", len(docs))
        for doc in docs:
            meeting_code: str = doc.value.get("meeting_code")
            document_id: str = doc.value.get("document_id")
            transcript_text: str = doc.value.get("text")
            provider: str = doc.value.get("provider")
            conversation: TranscriptConversation = ProcessorSupport.process_google_transcript(transcript_text, document_id, meeting_code)
            handler.handle_transcript(conversation)
            print(f"document added ",  provider, )
        # count_doc_summary = w.count(weaviate.WeaviateSchemas.DOCUMENT_SUMMARY)
        # count_doc = w.count(weaviate.WeaviateSchemas.DOCUMENT)
        # count_doc_text = w.count(weaviate.WeaviateSchemas.DOCUMENT_TEXT)   
        # print(f"number of entries in document summary: {count_doc_summary}")
        # print(f"number of entries in document: {count_doc}")
        # print(f"number of entries in document text: {count_doc_text}")
    finally:
        if w is not None:
            w.close()

def start():
    dotenv.load_dotenv()
    ProcessorSupport.kafka_listen(KafkaTopics.TRANSCRIPTS, "transcripts_processor", write_transcripts_to_vdb)


if __name__ == '__main__':
    start()