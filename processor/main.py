import json
from kafka import KafkaConsumer, TopicPartition
import os
import library.weaviate as weaviate
import traceback
import warnings
from py2neo import Graph, Node, Relationship

warnings.simplefilter("ignore", ResourceWarning)

def write_to_vdb(mapped: list) -> None:
        db = os.getenv("VECTOR_DB_HOST", "127.0.0.1")
        db_port = os.getenv("VECTOR_DB_PORT", "8080")
        print("Writing to VDB at " + db + ":" + db_port + " ... " + str(len(mapped)))
        w = None
        try:
            w = weaviate.Weaviate(db, db_port)
            for j,record in enumerate(mapped):
                #try:
                    email: dict = record.value
                    events = email.get('events', [])
                    email.pop('events', None)
                    print("=> Considering email " + str(j) + " of " + str(len(mapped)) + "...")
   
                    if email['body'] == None or email['body'] == '':
                        email['body'] = email['subject']
                    w.upsertChunkedText(email, weaviate.WeaviateSchemas.EMAIL_TEXT, weaviate.WeaviateSchemas.EMAIL, 'body')
                    print("upsertedchunked part is complete")
                    # print("events: ", event)
                    for event in events:
                        print("Upserting event " + str(event) + " on from " + str(email['from']))
                        if event.get('description') == None or event.get('description') == '':
                            event['description'] = event.get('summary', '')
                        w.upsertChunkedText(event, weaviate.WeaviateSchemas.EVENT_TEXT, weaviate.WeaviateSchemas.EVENT, 'description')
                        
            print(w.count(weaviate.WeaviateSchemas.EMAIL))
        finally:
            if w is not None:
                w.close()

def write_to_neo4j(events) -> None:
        db = os.getenv("NEO4J_DB_HOST", "127.0.0.1")
        db_port = os.getenv("NEO4J_DB_PORT", "8080")
        # url = "neo4j://localhost:7687"
        url = "neo4j://" + db + ":" + db_port
        username = "neo4j"
        password = "password"
        graph = Graph(url, auth=(username, password))
        print("Writing to Neo4j at " + ":" + url + " ... " + str(len(events)))
        person_list = []
        events_list = []
        attendance_list = []
        try:
            for record in events:
                event = record.value
                print("event: ", event)
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                eventName = event["summary"]
                event_dict = {"id": eventName, "starttime": start, "endtime": end}
                events_list.append(event_dict)
                attendees = event["attendees"]
                for item in attendees:
                    attendee = {"id": item["email"]}
                    rel_dict = {"person_id": item["email"], "event_id": event_dict["id"]}
                    attendance_list.append(rel_dict)
                    person_list.append(attendee)
            # Creating and merging Person nodes
            for person in person_list:
                node = Node("Person", id=person['id'])
                graph.merge(node, "Person", "id")


            # Creating and merging Event nodes
            for event in events_list:
                node = Node("Event", id=event['id'], starttime=event['starttime'], endtime=event['endtime'])
                graph.merge(node, "Event", "id")

            # Creating ATTENDS relationships
            for attend in attendance_list:
                person_node = graph.nodes.match("Person", id=attend['person_id']).first()
                event_node = graph.nodes.match("Event", id=attend['event_id']).first()
                rel = Relationship(person_node, "ATTENDS", event_node)
                graph.merge(rel)

            print("Data has been successfully added to the graph!")
                

        except TypeError as error:
            print(f"An error occurred: {error}")


def start():
    kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
    topic = os.getenv("KAFKA_TOPIC", "emails")
    print("Starting processor at " + kafka + " on topic " + topic + " ...")
    try:
        consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                group_id='processor',
                                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
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
                print("message: ", message)
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
            
    finally:
        print("Closing consumer")
        consumer.close()


def start_kafka_calendar():
    kafka = os.getenv("KAFKA_BROKER", "127.0.0.1:9092")
    topic = os.getenv("KAFKA_TOPIC", "calendar")
    print("Starting processor at " + kafka + " on topic " + topic + " ...")
    try:
        consumer = KafkaConsumer(bootstrap_servers=kafka, 
                                group_id='processor2',
                                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                                api_version="7.3.2")
        consumer.subscribe(topics=[topic])
        print("Subscribed to " + topic + ", waiting for messages...")

        count = 0

        key: TopicPartition = TopicPartition(topic=topic, partition=0)
        partitions = None
        message = None
        while partitions == None or len(partitions) == 0:
            print("IM here")
            partitions = consumer.partitions_for_topic(topic)
            print("now here: ", partitions)
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

                write_to_neo4j(message[key])
                print(" ... written to VDB")
            
            consumer.commit()
            
    finally:
        print("Closing consumer")
        consumer.close()


if __name__ == '__main__':
    start()
    start_kafka_calendar()