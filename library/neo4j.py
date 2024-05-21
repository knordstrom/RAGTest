from datetime import datetime
import dotenv
from neo4j import GraphDatabase
import os
import hashlib

class Neo4j:

    def __init__(self):
        dotenv.load_dotenv()
        self.db_host = os.getenv("NEO4J_DB_HOST", "localhost")
        self.db_port = os.getenv("NEO4J_DB_PORT", "7687")
        self.url = f"neo4j://{self.db_host}:{self.db_port}"
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j")
        self.driver = GraphDatabase.driver(self.url, auth=(self.username, self.password))

    def connect(self):
        print("url is: ", self.url)
        try:
            with self.driver.session() as session:
                session.run("MATCH () RETURN 1 LIMIT 1")
            print('Successfully connected')
        except Exception:
            print('Unsuccessful connection')

    def close(self):
        self.driver.close()

    def get_schedule(self, email: str, start_time: datetime, end_time: datetime) -> dict:
        query = """
        MATCH (person:Person {email: $email})
        MATCH (event:Event)-[invite:ATTENDS]-(person)
        MATCH (attendee:Person)-[attending:ATTENDS]-(event)
        WHERE event.end >= datetime($start_time) AND event.start <= datetime($end_time)
        RETURN DISTINCT person.name, person.email, event.name, event.description, event.start, event.end, invite.status, attendee.name, attendee.email, attending.status
        """
        print("Querying Neo4j with: " + query)
        with self.driver.session() as session:
            results = session.run(query, email=email, start_time=start_time.isoformat(), end_time=end_time.isoformat())
            print("Results were", results)
            return Neo4j.collate_schedule_response(results)

    def merge_node(self, label, identifier, properties):
        query = f"""
        MERGE (n:{label} {{{identifier}: $id}})
        ON CREATE SET n += $properties
        ON MATCH SET n += $properties
        """
        print(f"Merging node: {label} with properties {properties}")
        with self.driver.session() as session:
            session.run(query, id=properties[identifier], properties=properties)

    def create_relationship(self, start_node_label, start_node_key, start_node_value, rel_type, end_node_label, end_node_key, end_node_value, properties):
        query = f"""
        MATCH (start:{start_node_label} {{{start_node_key}: $start_node_value}})
        MATCH (end:{end_node_label} {{{end_node_key}: $end_node_value}})
        MERGE (start)-[r:{rel_type} {{id: $rel_id}}]->(end)
        ON CREATE SET r += $properties
        """
        with self.driver.session() as session:
            session.run(query, start_node_value=start_node_value, end_node_value=end_node_value, rel_id=properties['id'], properties=properties)

    def process_events(self, events):
        person_list = []
        events_list = []
        attendance_list = []

        for record in events:
            event = record.value
            event_dict = self.extract_event_info(event)
            events_list.append(event_dict)
            self.extract_attendees_info(event, event_dict, person_list, attendance_list)
        self.add_to_db(person_list, events_list, attendance_list)

    def extract_event_info(self, event):
        event_dict = {
            "id": event.get("id"),
            "status": event.get("status", ""),
            "recurring_id": event.get("recurringEventId", ""),
            "start": event["start"].get("dateTime", event["start"].get("date")),
            "end": event["end"].get("dateTime", event["end"].get("date")),
            "summary": event.get("summary", ""),
            "description": event.get("description", "")
        }
        return event_dict

    def extract_attendees_info(self, event, event_dict, person_list, attendance_list):
        for item in event.get("attendees", []):
            email = item.get("email", "")
            sha256 = hashlib.sha256()
            sha256.update(email.encode('utf-8'))
            attendee_id = sha256.hexdigest()
            attend_rel_id = attendee_id + event_dict["id"]
            invited_rel_id = event_dict["id"] + attendee_id

            attendee = {
                "id": attendee_id,
                "email": email,
                "name": item.get("displayName", ""),
                "response_status": item.get("responseStatus", "")
            }
            rel_dict = {
                "person_email": email,
                "event_id": event_dict["id"],
                "status": attendee["response_status"],
                "attend_rel_id": attend_rel_id,
                "invited_rel_id": invited_rel_id
            }
            attendance_list.append(rel_dict)
            person_list.append(attendee)

    def add_to_db(self, person_list, events_list, attendance_list):
        for person in person_list:
            self.merge_node("Person", "id", person)

        for event in events_list:
            self.merge_node("Event", "id", event)

        for attend in attendance_list:
            self.create_relationship("Person", "email", attend['person_email'], "ATTENDS", "Event", "id", attend['event_id'], {"id": attend["attend_rel_id"], "status": attend["status"]})
            self.create_relationship("Event", "id", attend['event_id'], "INVITED", "Person", "email", attend['person_email'], {"id": attend["invited_rel_id"], "status": attend["status"]})

    @staticmethod
    def collate_schedule_response(records):
        def key(record):
            return record['person.name'] + "||" + record['person.email'] + "||" + record['event.name'] + "||" + str(record['event.start']) + "||" + str(record['event.end'])

        collated = {}
        for record in records:
            record_dict = {}
            k = key(record)
            if k not in collated:
                record_dict['attendees'] = []
                record_dict['event.start'] = record['event.start'].isoformat()
                record_dict['event.end'] = record['event.end'].isoformat()
                collated[k] = record_dict
                
            if record['attendee.email'] != record['person.email']:
                collated[k]['attendees'].append({
                    'name': record['attendee.name'],
                    'email': record['attendee.email'],
                    'attending.status': record['attending.status']
                })

        response = list(collated.values())
        return sorted(response, key=lambda x: x['event.start'])