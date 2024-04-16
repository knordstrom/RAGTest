import json
from types import TracebackType
from kafka import KafkaConsumer, TopicPartition
import os
import library.weaviate as weaviate
import traceback

def write_to_vdb(mapped: list) -> None:
        db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
        db_port = os.getenv("VECTOR_DB_PORT", "8080")
        print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(mapped)))
        w = None
        try:
            w = weaviate.Weaviate(db, db_port)
            print("Weave")
            for j,record in enumerate(mapped):
                print("RRRRR " + str(type(record.value)) + " " + str(record.value))
                try:
                    email: dict = record.value
                    print("=> Considering email " + str(j) + " of " + str(len(mapped)) + "...")
                    print("Upserting email " + str(email) + " on from ")
                
                    if email['body'] == None or email['body'] == '':
                        email['body'] = email['subject']
                    w.upsertChunkedText(email, weaviate.WeaviateSchemas.EMAIL_TEXT, weaviate.WeaviateSchemas.EMAIL, 'body')
                except:           
                    print("Error: ")
                    traceback.print_stack()
            print(w.count(weaviate.WeaviateSchemas.EMAIL))
        finally:
            if w is not None:
                w.close()

def start():
    kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
    topic = os.getenv("KAFKA_TOPIC", "emails")
    print("Starting processor at " + kafka + " on topic " + topic + " ...")
    try:
        consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                group_id='processor',
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

                write_to_vdb(message[key])
                print(" ... written to VDB")
            
            consumer.commit()
            
    except Exception as e:
        print("Error: " + str(e))
    finally:
        print("Closing consumer")
        consumer.close()

if __name__ == '__main__':
    start()