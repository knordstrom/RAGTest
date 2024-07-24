import unittest
import os

from library.api_models import MeetingAttendee
from library.models.event import Event
from library.processor_support import EventRecordWrapper, ProcessorSupport
from library.weaviate_schemas import EmailParticipant

class TestEventExtracts(unittest.TestCase):

    def test_event_extract_invite1(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'invite1.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.event_id  == "ukte59phk6banfg9rtl4bo29h4@google.com"
            assert event.summary  == "Keith/Nick"
            assert event.description == "Keith/Nick"
            assert event.location == "Upslope Brewing Company\, 1898 S Flatiron Ct\, Boulder\, CO 80301\, USA"
            assert event.start.isoformat() == "2024-05-31T15:00:00-06:00"
            assert event.end.isoformat() == "2024-05-31T17:00:00-06:00"
            assert event.organizer == EmailParticipant(name='Nick Isaacs' , email='email1@location.com')
            assert event.status == "CONFIRMED"
            assert len(event.attendees) == 2
            assert MeetingAttendee(name = 'Nick Isaacs', email = 'email1@location.com') in event.attendees 
            assert MeetingAttendee(name = 'email2@myhouse.com', email = 'email2@myhouse.com') in event.attendees 

    def test_event_extract_invite2(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'invite2.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.event_id  == "20240602T191453Z-1@GALAXY-CALENDAR-EVENT-fe068b44-b99d-4b54-8dad-f27da0fd845b"
            assert event.summary  == "Katie:Keith"
            assert event.description  == "Katie:Keith"
            assert event.location  == "Phone call"
            assert event.start.isoformat()  == "2024-04-22T10:30:00-06:00"
            assert event.end.isoformat()  == "2024-04-22T11:00:00-06:00"
            assert event.organizer  == EmailParticipant(name='keith@myhouse.com' , email='keith@myhouse.com')
            assert event.status  == "CONFIRMED"
            assert len(event.attendees ) == 0

    def test_event_extract_standup(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'standup.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event: Event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.event_id  == "20240602T191044Z-1@GALAXY-CALENDAR-EVENT-4e44ff8b-6dd5-43d9-b438-eb822d136cde"
            assert event.summary  == "Cognimate Standup"
            assert event.description  == "-::~:~::~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~::~:~::-=0AJoin with Google Meet: https://meet.google.com/rdq-dzwe-stk=0AOr dial: (US) +1 413-648-4559 PIN: 934959535#=0AMore phone numbers: https://tel.meet/rdq-dzwe-stk?pin=3D3154749620907&hs=3D7=0A=0ALearn more about Meet at: https://support.google.com/a/users/answer/9282720=0A=0APlease do not edit this section.=0A-::~:~::~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~:~::~:~::-"
            assert event.location  is None, "No location should be included in the standup invvite"
            assert event.start.isoformat()  == "2024-05-30T18:00:00-06:00"
            assert event.end.isoformat()  == "2024-05-30T19:00:00-06:00"
            assert event.organizer  == EmailParticipant(name='keith@myhouse.com' , email='keith@myhouse.com')
            assert event.status  == "CONFIRMED"
            assert len(event.attendees ) == 4

            assert MeetingAttendee(name='keith@myhouse.com' , email='keith@myhouse.com') in event.attendees 
            assert MeetingAttendee(name='mithali@myhouse.com' , email='mithali@myhouse.com') in event.attendees 
            assert MeetingAttendee(name='pradeepj@myhouse.com' , email='pradeepj@myhouse.com') in event.attendees 
            assert MeetingAttendee(name='prakash@myhouse.com' , email='prakash@myhouse.com') in event.attendees 

    def test_event_extract_allday(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'allday.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event: Event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.event_id  == "20240602T191148Z-1@GALAXY-CALENDAR-EVENT-6b2940d0-4e20-42c4-b2dc-541dc9e05152"
            assert event.summary  == "Juneteenth"
            assert event.description  == "Public holiday"
            assert event.location  is None
            assert event.start.isoformat()  == "2024-06-19T00:00:00"
            assert event.end.isoformat()  == "2024-06-20T00:00:00"
            assert event.organizer  is None, "Juneteenth should have no organizer"
            assert event.status  == "CONFIRMED"
            assert len(event.attendees ) == 0
    
    def test_event_extract_sample1(self):
        file = os.path.join(os.path.dirname(__file__), '../../resources/events', 'sample1.ics')
        with open(file, 'r') as file:
            ics_file = file.read()
            event = Event.create(ics_file)
            print(event)

            assert event is not None

            assert event.event_id  == "040000008200E00074C5B7101A82E00800000000C0EAD578A994DA01000000000000000010000000A87945CED770314E896263731E214D0C"
            assert event.summary  == "Andrew Thompson <<>> Keith Nordstrom - Introduction to Hayden Data"             
            assert event.description .startswith("Looking forward to talking today Keith.\\n_______")
            assert event.location  == "Microsoft Teams Meeting"
            assert event.start.isoformat()  == "2024-04-22T12:00:00-06:00"
            assert event.end.isoformat()  == "2024-04-22T13:00:00-06:00"
            assert event.organizer  == EmailParticipant(name='Andrew Thompson' , email='andrew.t@company.com')
            assert event.status  == "CONFIRMED"
            assert len(event.attendees ) == 2
            assert MeetingAttendee(name='Gary Bresien' , email='gary@recruiter.com') in event.attendees 
            assert MeetingAttendee(name='keith@myhouse.com' , email='keith@myhouse.com') in event.attendees 

    def test_gsuite_event_from_ics(self):
        graph_event: EventRecordWrapper = ProcessorSupport.email_event_to_graph_event(Event(**self.ics_event_dict))
        for k in self.gsuite_event_dict.keys():
            print(f"Checking key {k}", k, "   ", graph_event.value.get(k), "    ", self.gsuite_event_dict[k])
            if k == "start" or k == "end":
                # there is an inconsistency in the values listed below. The ICS dicts list the tz as Etc/UTC when it is in -6:00
                assert graph_event.value.get(k)["dateTime"] == self.gsuite_event_dict[k]["dateTime"], f"Key {k} does not match"
            else:
                assert graph_event.value.get(k) == self.gsuite_event_dict[k], f"Key {k} does not match"

    ics_event_dict =  {
            "event_id":  "_6oq3ac1l69j32or1c5i3ep1g64pjgchm60pjcopb6or3ccpk6kpmadb274rm6chgccsmae1ocdh36chd74oj8d346ksmcbbgc5p78rj5e906atj5dpq2soridtn6upjp5phmur8",
            "summary": "Keith Nordstrom and Linda Coaching Meeting",
            "description": "\n\n\nDear Keith,\n\nThis is to confirm a meeting with your Randstad RiseSmart Coach has been \nscheduled.\n\n\n\nTopic: Uncover Your Opportunities \nLocation: +1 303-555-5555 \nWhen: 06/13/2024, 3:00 PM \nDuration: 30minute(s) \n\n\nTopic(s) to be discussed:\n\n\n * Uncover Your Opportunities \n\n\nWe request 24-hours' notice if you need to cancel or reschedule this meeting. \nIf you need to make changes, please log into your Randstad RiseSmart account\nhttps://apps.coach.com/secure/dashboard/show\n\n\n\n\nBest regards,\nYour Randstad RiseSmart Team \n\n\n\nIf you encounter any issues, please email our support team. \n(mailto:user.support@coach.com) \n\n\n2024 Randstad RiseSmart, Inc. All Rights Reserved\n",
            "location": "+1 303-555-5555",
            "start":  "2024-06-13T15:00:00-06:00",
            "end": "2024-06-13T15:30:00-06:00",
            "organizer": {
                "email": "linda@coach.net",
                "name": "Linda Jones"
            },
            "status": "confirmed",
            "attendees": [{
                "email": "keith@me.com",
                "name": "Keith Nordstrom",
            },
            {
                "email": "linda@coach.net",
                "name": "Linda Jones"
            }],
            "content": ""
        }

    gsuite_event_dict = {
        "attendees": [
            {
                "email": "keith@me.com",
            },
            {
                "email": "linda@coach.net",
            }
        ],
        "creator": {
            "email": "linda@coach.net"
        },
        "description": "\n\n\nDear Keith,\n\nThis is to confirm a meeting with your Randstad RiseSmart Coach has been \nscheduled.\n\n\n\nTopic: Uncover Your Opportunities \nLocation: +1 303-555-5555 \nWhen: 06/13/2024, 3:00 PM \nDuration: 30minute(s) \n\n\nTopic(s) to be discussed:\n\n\n * Uncover Your Opportunities \n\n\nWe request 24-hours' notice if you need to cancel or reschedule this meeting. \nIf you need to make changes, please log into your Randstad RiseSmart account\nhttps://apps.coach.com/secure/dashboard/show\n\n\n\n\nBest regards,\nYour Randstad RiseSmart Team \n\n\n\nIf you encounter any issues, please email our support team. \n(mailto:user.support@coach.com) \n\n\n2024 Randstad RiseSmart, Inc. All Rights Reserved\n",
        "end": {
            "dateTime": "2024-06-13T15:30:00-06:00",
            "timeZone": "Etc/UTC"
        },
        "id": "_6oq3ac1l69j32or1c5i3ep1g64pjgchm60pjcopb6or3ccpk6kpmadb274rm6chgccsmae1ocdh36chd74oj8d346ksmcbbgc5p78rj5e906atj5dpq2soridtn6upjp5phmur8",
        "location": "+1 303-555-5555",
        "organizer": {
            "email": "linda@coach.net"
        },
        "start": {
            "dateTime": "2024-06-13T15:00:00-06:00",
            "timeZone": "Etc/UTC"
        },
        "status": "confirmed",
        "summary": "Keith Nordstrom and Linda Coaching Meeting",
    }

