import datetime
import neo4j.time
import pytz


import unittest
import os

from library.models.event import Event
from library.data.local.neo4j import Neo4j

class TestNeo4j(unittest.TestCase):

    # Cypher query to create the data in the Neo4j database:
    #
    # CREATE (p1:Person {name: 'Keith Nordstrom',email:'keith@cognimate.ai'})
    # CREATE (p2:Person {name: 'Mithali Shashidhar',email:'mithali@cognimate.ai'})
    # CREATE (p3:Person {name: 'Prakash Aditham',email:'prakash@cognimate.ai'})
    # CREATE (p4:Person {name: 'Pradeep Javangula',email:'pradeep@cognimate.ai'})
    # CREATE (e1:Event {start:datetime('2024-05-06T17:00:00-06:00'), end:datetime('2024-05-06T17:30:00-06:00'),name:'Kickoff Meeting', description:'Getting everyone together to discuss the sofia project'})
    # CREATE (e2:Event {start:datetime('2024-05-08T17:00:00-06:00'), end:datetime('2024-05-08T17:30:00-06:00'),name:'Follow Up Meeting', description:"We need to meet to answer any questions anyone has about the pitch deck"})
    # CREATE (p1)-[:ATTENDS {status:"Unknown"}]->(e1)
    # CREATE (e1)-[:INVITED]->(p1)
    # CREATE (p2)-[:ATTENDS {status:"Declined"}]->(e1)
    # CREATE (e1)-[:INVITED]->(p2)
    # CREATE (p3)-[:ATTENDS {status:"Accepted"}]->(e1)
    # CREATE (e1)-[:INVITED]->(p3)
    # CREATE (p4)-[:ATTENDS {status:"Declined"}]->(e1)
    # CREATE (e1)-[:INVITED]->(p4)
    # CREATE (p1)-[:ATTENDS {status:"Accepted"}]->(e2)
    # CREATE (e2)-[:INVITED]->(p1)
    # CREATE (p2)-[:ATTENDS {status:"Accepted"}]->(e2)
    # CREATE (e2)-[:INVITED]->(p2)
    # CREATE (p3)-[:ATTENDS {status:"Accepted"}]->(e2)
    # CREATE (e2)-[:INVITED]->(p3)
    # CREATE (p4)-[:ATTENDS {status:"Accepted"}]->(e2)
    # CREATE (e2)-[:INVITED]->(p4)
    
    data = [{'person.name': 'Keith Nordstrom', 'person.email':'keith@cognimate.ai', 'event_id': 'a', 'event.name': 'Follow Up Meeting', 'organizer.name': 'Keith Nordstrom', 'organizer.email': 'keith@cognimate.ai', 'event.description': 'We need to meet to answer any questions anyone has about the pitch deck', 'event.start': neo4j.time.DateTime(2024, 5, 8, 17, 0, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'event.end': neo4j.time.DateTime(2024, 5, 8, 17, 30, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'invite.status': 'Accepted', 'attendee.name': 'Mithali Shashindar', 'attendee.email': 'mithali@cognimate.ai', 'attending.status': 'Accepted'}, 
        {'person.name': 'Keith Nordstrom', 'person.email':'keith@cognimate.ai', 'event_id': 'a', 'person.email':'keith@cognimate.ai', 'event.name': 'Follow Up Meeting', 'organizer.name': 'Keith Nordstrom', 'organizer.email': 'keith@cognimate.ai', 'event.description': 'We need to meet to answer any questions anyone has about the pitch deck', 'event.start': neo4j.time.DateTime(2024, 5, 8, 17, 0, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'event.end': neo4j.time.DateTime(2024, 5, 8, 17, 30, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'invite.status': 'Accepted', 'attendee.name': 'Keith Nordstrom', 'attendee.email': 'keith@cognimate.ai', 'attending.status': 'Accepted'}, 
        {'person.name': 'Keith Nordstrom', 'person.email':'keith@cognimate.ai', 'event_id': 'a', 'event.name': 'Follow Up Meeting', 'organizer.name': 'Keith Nordstrom', 'organizer.email': 'keith@cognimate.ai', 'event.description': 'We need to meet to answer any questions anyone has about the pitch deck', 'event.start': neo4j.time.DateTime(2024, 5, 8, 17, 0, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'event.end': neo4j.time.DateTime(2024, 5, 8, 17, 30, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'invite.status': 'Accepted', 'attendee.name': 'Pradeep Javangula', 'attendee.email': 'pradeep@cognimate.ai', 'attending.status': 'Accepted'}, 
        {'person.name': 'Keith Nordstrom', 'person.email':'keith@cognimate.ai', 'event_id': 'b', 'event.name': 'Kickoff Meeting', 'organizer.name': 'Pradeep Javangula', 'organizer.email': 'pradeep@cognimate.ai', 'event.description': 'Getting everyone together to discuss the sofia project', 'event.start': neo4j.time.DateTime(2024, 5, 6, 17, 0, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'event.end': neo4j.time.DateTime(2024, 5, 6, 17, 30, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'invite.status': 'Unknown', 'attendee.name': 'Mithali Shashindar', 'attendee.email': 'mithali@cognimate.ai', 'attending.status': 'Declined'}, 
        {'person.name': 'Keith Nordstrom', 'person.email':'keith@cognimate.ai', 'event_id': 'b', 'event.name': 'Kickoff Meeting', 'organizer.name': 'Pradeep Javangula', 'organizer.email': 'pradeep@cognimate.ai', 'event.description': 'Getting everyone together to discuss the sofia project', 'event.start': neo4j.time.DateTime(2024, 5, 6, 17, 0, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'event.end': neo4j.time.DateTime(2024, 5, 6, 17, 30, 0, 0, tzinfo=pytz.FixedOffset(-360)), 'invite.status': 'Unknown', 'attendee.name': 'Keith Nordstrom', 'attendee.email': 'keith@cognimate.ai', 'attending.status': 'Unknown'}]

    def test_collate_schedule_response(self):
        response: list[Event] = Neo4j.collate_schedule_response(self.data)
        print(response)
        assert len(response) == 2

        record = response[0]
        #Kickoff Meeting            Mithali Shashindar      Declined
        #Kickoff Meeting            Keith Nordstrom         Unknown

        assert record.organizer.name == 'Pradeep Javangula'
        assert record.organizer.email == 'pradeep@cognimate.ai'
        assert record.summary == 'Kickoff Meeting'
        assert record.description == 'Getting everyone together to discuss the sofia project'
        assert record.start == datetime.datetime.fromisoformat('2024-05-06T17:00:00.000000000-06:00')
        assert record.end == datetime.datetime.fromisoformat('2024-05-06T17:30:00.000000000-06:00')
        assert len(record.attendees) == 1
        assert record.attendees[0].name == 'Mithali Shashindar'
        assert record.attendees[0].email == 'mithali@cognimate.ai'
        assert record.attendees[0].status == 'Declined'

        #Follow Up Meeting          Mithali Shashindar      Accepted
        #Follow Up Meeting          Keith Nordstrom         Accepted
        #Follow Up Meeting          Pradeep Javangula       Accepted
        record = response[1]
        assert record.organizer.name == 'Keith Nordstrom'
        assert record.organizer.email == 'keith@cognimate.ai'
        assert record.summary == 'Follow Up Meeting'
        assert record.description == 'We need to meet to answer any questions anyone has about the pitch deck'
        assert record.start == datetime.datetime.fromisoformat('2024-05-08T17:00:00.000000000-06:00')
        assert record.end == datetime.datetime.fromisoformat('2024-05-08T17:30:00.000000000-06:00')
        assert len(record.attendees) == 2
        assert record.attendees[0].name == 'Mithali Shashindar'
        assert record.attendees[0].email == 'mithali@cognimate.ai'
        assert record.attendees[0].status == 'Accepted'
        assert record.attendees[1].name == 'Pradeep Javangula'
        assert record.attendees[1].email == 'pradeep@cognimate.ai'
        assert record.attendees[0].status == 'Accepted'