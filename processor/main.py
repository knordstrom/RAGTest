import json
from kafka import KafkaConsumer, TopicPartition
import os
import library.weaviate as weaviate
import traceback
import warnings
from py2neo import Graph, Node, Relationship
import hashlib

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
        db = os.getenv("NEO4J_DB_HOST", "docker-neo4j-1")
        db_port = os.getenv("NEO4J_DB_PORT", "7687")
        url = "neo4j://" + db + ":" + db_port
        username = "neo4j"
        password = "password"
        graph = Graph(url, auth=(username, password))
        try:
            graph.run("Match () Return 1 Limit 1")
            print('successfully connected')
        except Exception:
            print('unsuccessful connection')
        print("Writing to Neo4j at " + ":" + url + " ... " + str(len(events)))
        person_list = []
        events_list = []
        attendance_list = []
        try:
            for record in events:
                event = record.value
                print("event: ", event)
                status = ""
                start = ""
                end = ""
                event_summary = ""
                event_description = ""
                event_recurring_id = ""
                # get event information (meeting information)
                event_id = event["id"]
                if "status" in event:
                    status = event["status"]
                if "recurringEventId" in event:
                    event_recurring_id = event["recurringEventId"]
                if "start" in event:
                    start = event["start"].get("dateTime", event["start"].get("date"))
                if "end" in event:
                    end = event["end"].get("dateTime", event["end"].get("date"))
                if "summary" in event:
                    event_summary = event["summary"]
                if "description" in event:
                    event_description = event["description"]
                event_dict = {"id": event_id, "start": start, "end": end, "description": event_description,
                              "summary": event_summary, "recurring_id": event_recurring_id, "status": status}
                events_list.append(event_dict)
                # get person information
                attendees = event["attendees"]
                for item in attendees:
                    email = ""
                    name = ""
                    response_status = ""
                    attendee_id = ""
                    attend_rel_id = ""
                    invited_rel_id = ""
                    if "email" in item:
                        email = item["email"]
                        sha256 = hashlib.sha256()
                        sha256.update(email.encode('utf-8'))
                        attendee_id = sha256.hexdigest()
                        attend_rel_id = attendee_id + event_id
                        invited_rel_id = event_id + attendee_id
                    if "displayName" in item:
                        name = item["displayName"]
                    if "responseStatus" in item:
                        response_status = item["responseStatus"]
                    attendee = {"id": attendee_id, "email": email, "name": name, "response_status": response_status}
                    rel_dict = {"person_email": email, "event_id": event_dict["id"], "status":response_status, 
                                "attend_rel_id": attend_rel_id, "invited_rel_id": invited_rel_id}
                    attendance_list.append(rel_dict)
                    person_list.append(attendee)
            # Creating and merging Person nodes
            for person in person_list:
                node = Node("Person", id = person['id'], email = person['email'], name = person['name'], response_status = person['response_status'])
                graph.merge(node, "Person", "id")


            # Creating and merging Event nodes
            for event in events_list:
                node = Node("Event", id = event['id'], start = event['start'], end = event['end'], 
                description = event["description"], summary = event["summary"], recurring_id = event["recurring_id"],
                status = event["status"])
                graph.merge(node, "Event", "id")

            # Creating ATTENDS relationships
            for attend in attendance_list:
                person_node = graph.nodes.match("Person", email=attend['person_email']).first()
                event_node = graph.nodes.match("Event", id=attend['event_id']).first()
                attend_rel = Relationship(person_node, "ATTENDS", event_node, id = attend["attend_rel_id"], status = attend["status"])
                graph.create(attend_rel)
                invited_rel = Relationship(event_node, "INVITED", person_node, id = attend["invited_rel_id"])
                graph.create(invited_rel)
            print("Data has been successfully added to the graph!")
        except Exception as exception:
            print(f"An error occurred: {exception}")



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

                write_to_neo4j(message[key])
                print(" ... written to VDB")
            
            consumer.commit()
            
    finally:
        print("Closing consumer")
        consumer.close()


if __name__ == '__main__':
    start()