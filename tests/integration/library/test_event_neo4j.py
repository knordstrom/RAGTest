import ast
import time
import json
import os
from neo4j import Record
import pytest
import requests
from library import models, neo4j, weaviate as w
import library.handlers as h
from weaviate.classes.query import Filter
from requests.exceptions import ConnectionError

from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase

class WithValue:
    def __init__(self, value):
        self.value = value

class TestEventWeaviate(IntegrationTestBase):
    
    def is_responsive(self, url):
        try:
            print("Checking if service is responsive at ", url, " ... ")
            response = requests.get(url)
            if response.status_code == 200:
                print("Service is responsive")
                return True
        except ConnectionError:
            return False

    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services):
        # """Ensure that service is up and responsive."""

        port = docker_services.port_for("neo4j", 7575)
        url = "http://{}:{}".format(docker_ip, port)
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.1, check=lambda: self.is_responsive(url)
        )
        return {
            'url': url,
            'host': docker_ip,
            'port': "7688"
        }
    
    def test_event_model_create(self, service):
        graph = neo4j.Neo4j(service['host'], service['port'], "bolt", "neo4j", "password")
        graph.connect()

        graph.process_events([WithValue(self.event1), WithValue(self.event2)])

        response = graph.query("MATCH (n)-[r]->(b) RETURN n, r, b")

        result: list[Record] = [r for r in response.records]

        emails ={}
        events = {}
        items = []
        for saved in result:
            if saved['n'].labels == {'Person'}:
                emails[saved['n']['email']] = saved['n']['name']
                item = f"{saved['n']['name']} {saved['r'].type} {saved['b']['summary']}"
                items.append(item)
            elif saved['n'].labels == {'Event'}:
                events[saved['n']['summary']] = saved['n']['location']
                item = f"{saved['n']['summary']} {saved['r'].type} {saved['b']['name']}"
                items.append(item)

            print("       ---", saved)


        assert len(result) == 6    # 2 events and 2 people
        assert len(events) == 2
        assert 'linda@yourhouse.com' in emails.keys()
        assert 'keith@myhouse.com' in emails.keys()
        assert len(events) == 2
        assert 'Stay at Holiday Inn Express & Suites Grand Junction' in events.keys()
        assert 'Keith Nordstrom and Linda Coaching Meeting' in events.keys()
        assert len(items) == 6
        assert 'keith@myhouse.com ATTENDS Stay at Holiday Inn Express & Suites Grand Junction' in items
        assert 'keith@myhouse.com ATTENDS Keith Nordstrom and Linda Coaching Meeting' in items
        assert 'linda@yourhouse.com ATTENDS Keith Nordstrom and Linda Coaching Meeting' in items
        assert 'Stay at Holiday Inn Express & Suites Grand Junction INVITED keith@myhouse.com' in items
        assert 'Keith Nordstrom and Linda Coaching Meeting INVITED keith@myhouse.com' in items
        assert 'Keith Nordstrom and Linda Coaching Meeting INVITED linda@yourhouse.com' in items
    
    event1 = {"attendees":[{"email":"keith@myhouse.com","responseStatus":"accepted","self":True}],
               "created":"2024-05-31T18:53:21.000Z",
               "creator":{"email":"keith@myhouse.com","self":True},
               "description":"To see detailed information for automatically created events like this one, use the official Google Calendar app. https://g.co/calendar\n\nThis event was created from an email you received in Gmail. https://mail.google.com/mail?extsrc=cal&plid=ACUX6DOl4H-PtpOsoX5m77yAxhVXTw07SWw6RCY\n",
               "end":{"date":"2024-06-07"},
               "etag":"\"3434363203618000\"",
               "eventType":"default",
               "guestsCanInviteOthers":False,
               "htmlLink":"https://www.google.com/calendar/event?eid=YjZyaWQ1dXNkMWw1M3FzNzU2cW5mYjluaTQga2VpdGhAbWFkc3luYy5jb20",
               "iCalUID":"b6rid5usd1l53qs756qnfb9ni4@google.com",
               "id":"b6rid5usd1l53qs756qnfb9ni4",
               "kind":"calendar#event",
               "location":"Holiday Inn Express & Suites Grand Junction, Grand Junction",
               "organizer":{"email":"unknownorganizer@calendar.google.com"},"privateCopy":True,
               "reminders":{"useDefault":False},
               "sequence":0,
               "source":{"title":"","url":"https://mail.google.com/mail?extsrc=cal&plid=ACUX6DOl4H-PtpOsoX5m77yAxhVXTw07SWw6RCY"},
               "start":{"date":"2024-06-05"},
               "status":"confirmed",
               "summary":"Stay at Holiday Inn Express & Suites Grand Junction",
               "transparency":"transparent",
               "updated":"2024-05-31T18:53:21.809Z",
               "visibility":"private"}
    
    event2 = {
        "attendees": [
        {
            "email": "keith@myhouse.com",
            "responseStatus": "needsAction",
            "self": True
        },
        {
            "email": "linda@yourhouse.com",
            "organizer": True,
            "responseStatus": "accepted"
        }
        ],
        "created": "2024-05-29T18:05:33.000Z",
        "creator": {
        "email": "linda@yourhouse.com"
        },
        "description": "\n\n\nDear Keith,\n\nThis is to confirm a meeting with your Randstad RiseSmart Coach has been \nscheduled.\n\n\n\nTopic: Develop Your Messaging \nLocation: +1 303-544-9225 \nWhen: 06/07/2024, 11:00 AM \nDuration: 30minute(s) \n\n\nTopic(s) to be discussed:\n\n\n * Develop Your Messaging \n\n\nWe request 24-hours' notice if you need to cancel or reschedule this meeting. \nIf you need to make changes, please log into your Randstad RiseSmart account\nhttps://apps.risesmart.com/secure/dashboard/show\n\n\n\n\nBest regards,\nYour Randstad RiseSmart Team \n\n\n\nIf you encounter any issues, please email our support team. \n(mailto:user.support@risesmart.com) \n\n\n2024 Randstad RiseSmart, Inc. All Rights Reserved\n",
        "end": {
        "dateTime": "2024-06-07T11:30:00-06:00",
        "timeZone": "Etc/UTC"
        },
        "etag": "\"3434011870372000\"",
        "eventType": "default",
        "htmlLink": "https://www.google.com/calendar/event?eid=XzZvcTNhYzFsNjlqMzJvcjFjNWkzZXAxZzY0cGpnY2htNjBwamNvcGI2b3IzYWRwbWNrcjY4cDFrNmdxM2FvaG1jOHFtYW85bTZwaGo2YzFkNzFqMzhwMW9jbGdtYWJiZ2M1cDc4cmo1ZTkwNmF0ajVkcHEyc29yaWR0bjZ1cGpwNXBobXVyOCBrZWl0aEBtYWRzeW5jLmNvbQ",
        "iCalUID": "645052f1caad7d013826036c+66576e6dd4445b6b5ea66c30-8f4d8eae-partner@event.cronofy.com",
        "id": "_6oq3ac1l69j32or1c5i3ep1g64pjgchm60pjcopb6or3adpmckr68p1k6gq3aohmc8qmao9m6phj6c1d71j38p1oclgmabbgc5p78rj5e906atj5dpq2soridtn6upjp5phmur8",
        "kind": "calendar#event",
        "location": "+1 303-544-9225",
        "organizer": {
        "email": "linda@yourhouse.com"
        },
        "reminders": {
        "useDefault": True
        },
        "sequence": 1717005933,
        "start": {
        "dateTime": "2024-06-07T11:00:00-06:00",
        "timeZone": "Etc/UTC"
        },
        "status": "confirmed",
        "summary": "Keith Nordstrom and Linda Coaching Meeting",
        "updated": "2024-05-29T18:05:35.186Z"
    }
