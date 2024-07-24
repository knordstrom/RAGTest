from datetime import datetime
from typing import Any
import dotenv
from neo4j import GraphDatabase
import os

import neo4j.time

from library.person import Person
from library.utils import Utils
from library.employee import Employee
from library.weaviate_schemas import Event as WeaviateEvent
from library.models.event import Event

class EventPersonRelationships:
    attendance_map = {}
    person_map = {}
    organizer_map = {}

    @property
    def attendance_list(self):
        return list(self.attendance_map.values())
    
    @property
    def person_list(self):
        return list(self.person_map.values())
    
    def add_attendee(self, person_email, event_id, status, name):
        p = Person(name, person_email)
        attendee_id = p.identifier()
        attend_rel_id = attendee_id + event_id
        invited_rel_id = event_id + attendee_id

        attendee = p.to_dict()

        rel_dict = {
            "person_email": person_email,
            "event_id": event_id,
            "status": status,
            "attend_rel_id": attend_rel_id,
            "invited_rel_id": invited_rel_id
        }
        self.attendance_map[attend_rel_id] = rel_dict
        self.person_map[attendee_id] = attendee

class Neo4j:

    PERSON = "Person"
    EVENT = "Event"

    def __init__(self, host = None, port = None, protocol = None, user = None, password = None):
        dotenv.load_dotenv(dotenv_path = os.path.join(os.path.dirname(__file__), '../.env'))
        protocol = os.getenv("NEO4J_PROTOCOL", "bolt") if protocol is None else protocol
        self.db_host = os.getenv("NEO4J_DB_HOST", "localhost") if host is None else host
        self.db_port = os.getenv("NEO4J_DB_PORT", "7687") if port is None else port
        self.url = f"{protocol}://{self.db_host}:{self.db_port}"
        self.username = os.getenv("NEO4J_USERNAME", "neo4j") if user is None else user
        self.password = os.getenv("NEO4J_PASSWORD", "neo4j") if password is None else password
        self.driver = GraphDatabase.driver(self.url, auth=(self.username, self.password))
        self.connect()

    def connect(self):
        print("url is: ", self.url)
        try:
            with self.driver.session() as session:
                session.run("MATCH () RETURN 1 LIMIT 1")
            print('Successfully connected')
        except Exception as inst:
            print('Unsuccessful connection')
            print(type(inst))    # the exception type
            print(inst.args)     # arguments stored in .args
            print(inst)  

    def close(self):
        self.driver.close()

    def query(self, query):
        return self.driver.execute_query(query)

    def get_schedule(self, email: str, start_time: datetime, end_time: datetime) -> list[Event]:
        query = """
        MATCH (person:Person {email: $email})
        MATCH (event:Event)-[invite:INVITED]-(person)
        MATCH (attendee:Person)-[attending:ATTENDS]-(event)
        MATCH (event)-[r:ORGANIZED_BY]-(organizer:Person)
        WHERE datetime(event.end) >= datetime($start_time) AND datetime(event.start) <= datetime($end_time)
        RETURN DISTINCT person.name, person.email, event.id, event.name, event.description, event.start, event.end, event.recurring_id, invite.status, attendee.name, attendee.email, attending.status, organizer.name, organizer.email
        """
        print("Querying Neo4j with: " + query)
        with self.driver.session() as session:
            results = session.run(query, email=email, start_time=start_time.astimezone().isoformat(), end_time=end_time.astimezone().isoformat())
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
        print(f"Creating relationship: {rel_type} between {start_node_label} {start_node_value} and {end_node_label} {end_node_value}")
        with self.driver.session() as session:
            session.run(query, start_node_value=start_node_value, end_node_value=end_node_value, rel_id=properties['id'], properties=properties)

    def process_org_chart(self, org: list[Employee]):
        # performance: do without recursion?

        for employee in org:
            person = employee.to_dict()
            self.merge_node(self.PERSON, "id", person)
            self.process_org_chart(employee.reports)
            for sub in employee.reports:
                report = sub.to_dict()
                self.create_relationship(self.PERSON, "id", person["id"], "MANAGES", self.PERSON, "id", report["id"], {"id": person["id"] + report["id"]})
                self.create_relationship(self.PERSON, "id", report["id"], "REPORTS_TO", self.PERSON, "id", person["id"], {"id": report["id"] + person["id"]})
                     

    #### Events ####
    def process_events(self, events: list[Event]):
        """Processes a list of Google API calendar events and adds them, plus their atttendees, to the Neo4j database."""

        events_list = []
        relationships = EventPersonRelationships()

        for record in events:
            event = record.value
            event_dict = self.extract_event_info(event)
            events_list.append(event_dict)
            self.extract_attendees_info(event, event_dict, relationships)
        self.add_to_db(events_list, relationships)

    def extract_event_info(self, event):
        event_dict = {
            "id": event.get("id"),
            "status": event.get("status", ""),
            "recurring_id": event.get("recurringEventId", ""),
            "start": event["start"].get("dateTime", event["start"].get("date")),
            "end": event["end"].get("dateTime", event["end"].get("date")),
            "name": event.get("summary", ""),
            "description": event.get("description", ""),
            "summary": event.get("summary", ""),
        }
        return event_dict

    def extract_attendees_info(self, event: dict, event_dict: dict, relationships: EventPersonRelationships):
        for item in event.get("attendees", []):
            email = item.get("email", "")
            relationships.add_attendee(email, event_dict["id"], item.get("responseStatus", "Unknown"), item.get("displayName", email))
        relationships.organizer_map[event_dict["id"]] = event.get("organizer", {})

    def add_to_db(self, events_list, relationships: EventPersonRelationships):
        for person in relationships.person_list:
            self.merge_node(self.PERSON, "id", person)

        for event in events_list:
            self.merge_node(self.EVENT, "id", event)

        for attend in relationships.attendance_list:
            self.create_relationship(self.PERSON, "email", attend['person_email'], "ATTENDS", self.EVENT, "id", attend['event_id'], {"id": attend["attend_rel_id"], "status": attend["status"]})
            self.create_relationship(self.EVENT, "id", attend['event_id'], "INVITED", self.PERSON, "email", attend['person_email'], {"id": attend["invited_rel_id"], "status": attend["status"]})

        for event_id, organizer in relationships.organizer_map.items():
            self.create_relationship(self.PERSON, "email", organizer['email'], "ORGANIZES", self.EVENT, "id", event_id, {"id": 'organize' + event_id + organizer['email']})
            self.create_relationship(self.EVENT, "id", event_id, "ORGANIZED_BY", self.PERSON, "email", organizer['email'], {"id": 'organize' + event_id + organizer['email']})
            
            
    @staticmethod
    def collate_schedule_response(records: list[dict[str, Any]]) -> list[Event]:
        def key(record):
            t1 = datetime.fromisoformat(record['event.start']) if type(record['event.start']) == str  else record['event.start']
            t2 = datetime.fromisoformat(record['event.end']) if type(record['event.end']) == str else record['event.end']
            start = t1.strftime("%s")
            end = t2.strftime("%s")
            return record['person.email'] + "||" + str(record['event.name']) + "||" + str(start) + "||" + str(end)

        collated = {}
        for record in records:
            k = key(record)
            if k not in collated:   
                print("     => Key is: ", k)       
                collated[k] = Neo4j.create_new_record(record)              
            if record['attendee.email'] != record['person.email']:
                print("             Adding attendee", record['attendee.email'], record['event.name'], record['attending.status'], 'to', k)
                collated[k]['attendees'].append(Neo4j.create_attendee(record))

        print()
        print("Collated is: ", collated)
        print()
        return Neo4j.finalize_schedule_response(list(collated.values()))
    

    @staticmethod
    def create_attendee(record: dict) -> dict :
        return {
                    'name': record['attendee.name'],
                    'email': record['attendee.email'],
                    'status': record['attending.status']
                }

    @staticmethod
    def create_new_record(record: dict) -> dict:
        record_dict = {}
        record_dict.update(record)
        record_dict['attendees'] = []
        Utils.rename_key(record_dict, 'event.id', 'event_id')
        Utils.rename_key(record_dict, 'event.start', 'start', lambda x: x.isoformat() if type(x) == datetime else x)
        Utils.rename_key(record_dict, 'event.end', 'end', lambda x: x.isoformat() if type(x) == datetime else x)
        Utils.rename_key(record_dict, 'event.description', 'description')
        Utils.rename_key(record_dict, 'event.recurring_id', 'recurring_id')
        Utils.rename_key(record_dict, 'event.name', 'name')
        Utils.rename_key(record_dict, 'event.location', 'location')
        return record_dict
    
    @staticmethod
    def handle_time(value) -> datetime:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        elif isinstance(value, neo4j.time.DateTime):
            return value.to_native()
        else:
            return value
            
    @staticmethod
    def finalize_schedule_response(response: list[dict[str, any]]) -> list[Event]:
        result: list[Event] = []
        for item in response:
            item['person'] = {
                'name': item['person.name'],
                'email': item['person.email'],
                'status': item['invite.status'] 
            }
            item['organizer'] = {
                'name': item['organizer.name'],
                'email': item['organizer.email'],
            }

            item['start'] = Neo4j.handle_time(item['start'])
            item['end'] = Neo4j.handle_time(item['end'])
            
            for k in ['person.name', 'person.email', 'organizer.name', 'organizer.email', 'attendee.name', 'attendee.email', 
                      'attending.status', 'invite.status']:
                item.pop(k)
            
            item['summary'] = item.get('name')
            print("ITEM", item)
            result.append(Event(**item))

        return sorted(result, key=lambda x: x.start)
    