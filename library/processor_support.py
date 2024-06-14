import datetime
import datetime
import json
import os
from library import weaviate
from kafka import KafkaConsumer, TopicPartition

from library.enums.kafka_topics import KafkaTopics

class EventRecordWrapper:
    def __init__(self, value: dict):
        self.value = value

class ProcessorSupport:

    def email_event_to_graph_event(email_event: dict) -> dict:
        event = {
            'id': email_event.get('event_id'),
            'location': email_event.get('location'),
            'description': email_event.get('description'),
            'summary': email_event.get('summary'),
            'status': email_event.get('status')
        }

        event['creator'] = {
            'email': email_event.get('organizer', {}).get('email')
        }
        event['organizer'] = event["creator"]
        event['attendees'] = [{"email": e.get("email")} for e in email_event.get('attendees', [])]

        start_date = datetime.datetime.fromisoformat(email_event.get('start'))
        end_date = datetime.datetime.fromisoformat(email_event.get('end'))

        event['start'] = {
            "dateTime": start_date.isoformat(),
            "timeZone": "Etc/UTC" #start_date.tzname()
        }
        event['end'] = {
            "dateTime": end_date.isoformat(),
            "timeZone":  "Etc/UTC" #end_date.tzname()
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
    def kafka_listen(default_topic: KafkaTopics, group: str, endpoint: callable):
        kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
        topic = os.getenv("KAFKA_TOPIC", default_topic.value)
        topic = os.getenv("KAFKA_TOPIC", default_topic.value)
        print("Starting processor at " + kafka + " on topic " + topic + " ...")
        try:
            consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                    group_id=group,
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