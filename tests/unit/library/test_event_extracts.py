import unittest
import os

from library.models import Event

class TestEventExtracts(unittest.TestCase):

    def test_event_extract_invite1(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'invite1.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.get('event_id') == "ukte59phk6banfg9rtl4bo29h4@google.com"
            assert event.get('summary') == "Keith/Nick"
            assert event.get('description') == "Keith/Nick"
            assert event.get('location') == "Upslope Brewing Company\, 1898 S Flatiron Ct\, Boulder\, CO 80301\, USA"
            assert event.get('start') == "2024-05-31T15:00:00-06:00"
            assert event.get('end') == "2024-05-31T17:00:00-06:00"
            assert event.get('organizer') == {'name': 'Nick Isaacs', 'email': 'email1@location.com'}
            assert event.get('status') == "CONFIRMED"
            assert len(event.get('attendees')) == 2
            assert {'name': 'Nick Isaacs', 'email': 'email1@location.com'} in event.get('attendees')
            assert {'name': 'email2@myhouse.com', 'email': 'email2@myhouse.com'} in event.get('attendees')

    def test_event_extract_invite2(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'invite2.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.get('event_id') == "20240602T191453Z-1@GALAXY-CALENDAR-EVENT-fe068b44-b99d-4b54-8dad-f27da0fd845b"
            assert event.get('summary') == "Katie:Keith"
            assert event.get('description') == "Katie:Keith"
            assert event.get('location') == "Phone call"
            assert event.get('start') == "2024-04-22T10:30:00-06:00"
            assert event.get('end') == "2024-04-22T11:00:00-06:00"
            assert event.get('organizer') == {'name': 'keith@myhouse.com', 'email': 'keith@myhouse.com'}
            assert event.get('status') == "CONFIRMED"
            assert len(event.get('attendees')) == 0

    def test_event_extract_standup(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'standup.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.get('event_id') == "20240602T191044Z-1@GALAXY-CALENDAR-EVENT-4e44ff8b-6dd5-43d9-b438-eb822d136cde"
            assert event.get('summary') == "Cognimate Standup"
            assert event.get('description') == "-::~:~::~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~::~:~::-=0AJoin with Google Meet: https://meet.google.com/rdq-dzwe-stk=0AOr dial: (US) +1 413-648-4559 PIN: 934959535#=0AMore phone numbers: https://tel.meet/rdq-dzwe-stk?pin=3D3154749620907&hs=3D7=0A=0ALearn more about Meet at: https://support.google.com/a/users/answer/9282720=0A=0APlease do not edit this section.=0A-::~:~::~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~::~:~::-"
            assert event.get('location') is None, "No location should be included in the standup invvite"
            assert event.get('start') == "2024-05-30T18:00:00-06:00"
            assert event.get('end') == "2024-05-30T19:00:00-06:00"
            assert event.get('organizer') == {'name': 'keith@myhouse.com', 'email': 'keith@myhouse.com'}
            assert event.get('status') == "CONFIRMED"
            assert len(event.get('attendees')) == 4

            assert {'name': 'keith@myhouse.com', 'email': 'keith@myhouse.com'} in event.get('attendees')
            assert {'name': 'mithali@myhouse.com', 'email': 'mithali@myhouse.com'} in event.get('attendees')
            assert {'name': 'pradeepj@myhouse.com', 'email': 'pradeepj@myhouse.com'} in event.get('attendees')
            assert {'name': 'prakash@myhouse.com', 'email': 'prakash@myhouse.com'} in event.get('attendees')

    def test_event_extract_allday(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'allday.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.get('event_id') == "20240602T191148Z-1@GALAXY-CALENDAR-EVENT-6b2940d0-4e20-42c4-b2dc-541dc9e05152"
            assert event.get('summary') == "Juneteenth"
            assert event.get('description') == "Public holiday"
            assert event.get('location') is None
            assert event.get('start') == "2024-06-19"
            assert event.get('end') == "2024-06-20"
            assert event.get('organizer') is None, "Juneteenth should have no organizer"
            assert event.get('status') == "CONFIRMED"
            assert len(event.get('attendees')) == 0
    
    def test_event_extract_sample1(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'sample1.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.get('event_id') == "040000008200E00074C5B7101A82E00800000000C0EAD578A994DA01000000000000000010000000A87945CED770314E896263731E214D0C"
            assert event.get('summary') == "Andrew Thompson <<>> Keith Nordstrom - Introduction to Hayden Data"             
            assert event.get('description').startswith("Looking forward to talking today Keith.\\n_______")
            assert event.get('location') == "Microsoft Teams Meeting"
            assert event.get('start') == "2024-04-22T12:00:00-06:00"
            assert event.get('end') == "2024-04-22T13:00:00-06:00"
            assert event.get('organizer') == {'name': 'Andrew Thompson', 'email': 'andrew.t@company.com'}
            assert event.get('status') == "CONFIRMED"
            assert len(event.get('attendees')) == 2
            assert {'name': 'Gary Bresien', 'email': 'gary@recruiter.com'} in event.get('attendees')
            assert {'name': 'keith@myhouse.com', 'email': 'keith@myhouse.com'} in event.get('attendees')

