import datetime
import datetime
import json
import os
from library import weaviate, weaviate_schemas
from kafka import KafkaConsumer, TopicPartition
from collections.abc import Callable
from library.api_models import MeetingAttendee, TranscriptConversation, TranscriptLine
from library.enums.kafka_topics import KafkaTopics

class EventRecordWrapper:
    def __init__(self, value: dict):
        self.value = value

class ProcessorSupport:

    def email_event_to_graph_event(email_event: weaviate_schemas.Event, attendees: list[MeetingAttendee]) -> dict:
        event = {
            'id': email_event.event_id,
            'location': email_event.location,
            'description': email_event.description,
            'summary': email_event.summary,
            # 'status': email_event.status
        }

        event['creator'] = {
            'email': email_event.sender
        }
        event['organizer'] = event["creator"]
        event['attendees'] = [e.model_dump() for e in attendees]

        start_date = email_event.start
        end_date = email_event.end

        event['start'] = {
            "dateTime": start_date.isoformat(),
            "timeZone": start_date.tzname()
        }
        event['end'] = {
            "dateTime": end_date.isoformat(),
            "timeZone": end_date.tzname()
        }
        return EventRecordWrapper(event)

    @staticmethod
    def write_to_vdb(mapped: list, endpoint: callable) -> None:
        db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
        db_port = os.getenv("VECTOR_DB_PORT", "8080")
        print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(mapped)))
        w = None
        try:
            w = weaviate.Weaviate(db, db_port)
            for j,record in enumerate(mapped):
                thing: dict = record.value
                endpoint(thing)     
        finally:
            if w is not None:
                w.close()

    @staticmethod
    def kafka_listen(default_topic: KafkaTopics, group: str, endpoint: callable):
        kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
        topic = os.getenv("KAFKA_TOPIC", default_topic.value)
        topic = os.getenv("KAFKA_TOPIC", default_topic.value)
        print("Starting processor at " + kafka + " on topic " + topic + " ...")
        try:
            consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                    group_id=group,
                                    api_version="7.3.2",
                                    value_deserializer=lambda v: json.loads(v.decode('utf-8')))
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
                    message: dict = consumer.poll(timeout_ms=2000)
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

    @staticmethod
    def json_file_listen(file: str, endpoint: callable):
        print("Starting file processor on " + file + " ...")
        try:
            with open(file, 'r') as f:
                text = f.read()
                obj = json.loads(text)
                for j,record in enumerate(obj):
                    thing: dict = record
                    endpoint(thing)
                
        finally:
            print("Closing file")

    @staticmethod
    def process_google_transcript(transcript_text: str, document_id: str, meeting_code: str) -> TranscriptConversation:
        lines = transcript_text.splitlines()  
        title = lines[0]    
        attendees: list[str] = []
        transcript: list[str] = []

        if lines[1].startswith("Attendees"): 
            attendees = lines[2].split(",")
        if lines[3].startswith("Transcript"):
            transcript = lines[5:]

        transcript_entries = []
        ordinal: int = 0
        for line in transcript:
            try:
                [sender, comment] = line.split(":", 1)
                sender = sender.strip()
                comment = comment.strip()
                if sender in attendees:
                    transcript_entries.append(TranscriptLine(speaker=sender, text=comment, ordinal=ordinal))
                    ordinal += 1
            except ValueError:
                pass
            
        return TranscriptConversation(transcript_id=document_id, title=title, attendee_names=attendees, 
            provider="google", conversation=transcript_entries, meeting_code = meeting_code)   