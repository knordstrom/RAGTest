import ast
from library.models import message    
from library.api_models import MeetingAttendee
from library.gsuite import GmailLogic, GSuiteServiceProvider
import pytest
import unittest
import os

from library.weaviate_schemas import EmailParticipant

class TestMessage(unittest.TestCase):

    resource = os.path.dirname(__file__) + "/../../resources/sample_email.json"
    def test_message_structure(self):
        if os.path.exists(self.resource):
            with open(self.resource, "r") as email_json:
                #four messages in the file
                email_obj = self.next_email_obj(email_json)
                self.validate_first_mssage(email_obj)
                
                email_obj = self.next_email_obj(email_json)
                self.validate_second_message(email_obj)

                email_obj = self.next_email_obj(email_json)
                self.validate_third_message(email_obj)

                email_obj = self.next_email_obj(email_json)
                self.validate_fourth_message(email_obj)
                
        else:
            print("File " +  + " not found")
            assert False

    def next_email_obj(self, email_json):
        return message.Message.from_gsuite_payload(ast.literal_eval(email_json.readline()))


    def validate_first_mssage(self, email_obj: message.Message):
        assert email_obj.email_id == '18ea11b72cb9b7e5'
        assert email_obj.history_id == '8009515'
        assert email_obj.thread_id == '18ea11b72cb9b7e5'
        assert email_obj.labels == ['UNREAD', 'CATEGORY_UPDATES', 'INBOX']
        assert email_obj.to == [EmailParticipant(name='soandso@youremail.com', email='soandso@youremail.com')]
        assert email_obj.cc == []
        assert email_obj.bcc == []
        assert email_obj.subject == 'Latest News from My Portfolios'
        assert email_obj.sender == EmailParticipant(email='fool@motley.fool.com', name='The Motley Fool')
        assert email_obj.date.isoformat().startswith('2024-04-02T17:18:34')
        assert str(email_obj.body)[0:35:1] == 'Daily Update        The Motley Fool'
    
    def validate_second_message(self, email_obj: message.Message):
        assert email_obj.email_id == '18eb9e11501a6c78'
        assert email_obj.history_id == '8022615'
        assert email_obj.thread_id == '18eb9e11501a6c78'
        assert email_obj.labels == ['UNREAD', 'CATEGORY_UPDATES', 'INBOX']
        assert email_obj.to == [EmailParticipant(name='soandso@youremail.com', email='soandso@youremail.com')]
        assert email_obj.cc == []
        assert email_obj.bcc == []
        assert email_obj.subject == 'The French Whisperer just shared: "Ghost Ships, WITH Wave Sounds"'
        assert email_obj.sender == EmailParticipant(email='bingo@patreon.com', name='Patreon')
        assert email_obj.date.isoformat().startswith('2024-04-07T12:45:19')
        assert str(email_obj.body)[0:33:1] == 'The French Whisperer just shared:'

    def validate_third_message(self, email_obj: message.Message):
        assert email_obj.email_id == '18eba138f3178250'
        assert email_obj.history_id == '8022873'
        assert email_obj.thread_id == '18eba138f3178250'
        assert email_obj.labels == ['UNREAD', 'IMPORTANT', 'CATEGORY_UPDATES', 'INBOX']
        assert email_obj.to == [EmailParticipant(email='soandso@youremail.com', name='Keith')]
        assert email_obj.cc == []
        assert email_obj.bcc == []
        assert email_obj.subject == 'Appointment reminder for Tuesday, April 9th'
        assert email_obj.sender == EmailParticipant(email='yourprovider@simplepractice.com', name='Doctor Appointment')
        assert email_obj.date.isoformat().startswith('2024-04-07T13:40:26')
        assert str(email_obj.body) == ''

    def validate_fourth_message(self, email_obj: message.Message):
        assert email_obj.email_id == '18f06e3e9f0415ae'
        assert email_obj.history_id == '8062798'
        assert email_obj.thread_id == '18f06e3e9f0415ae'
        assert email_obj.labels == ['IMPORTANT', 'CATEGORY_PERSONAL', 'INBOX']
        assert email_obj.to == [EmailParticipant(name='"soandso@youremail.com"', email='soandso@youremail.com')]
        assert email_obj.cc == []
        assert email_obj.bcc == []
        assert email_obj.subject == 'Some Person <<>> Keith - Introduction to Company Data'
        assert email_obj.sender == EmailParticipant(email='someguy@dataco.com', name='Some Person')
        assert email_obj.date.isoformat().startswith('2024-04-22T11:39:08')
        assert str(email_obj.body)[0:32:1] == 'Looking forward to talking today'
        assert(len(email_obj.events)) != 0
        assert(email_obj.events[0].content[0:15:1]) == "BEGIN:VCALENDAR"



class TestICal(unittest.TestCase):


    simple = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:Spark
CALSCALE:GREGORIAN
METHOD:REPLY
BEGIN:VEVENT
DTSTART;VALUE=DATE-TIME:20240501T160000Z
DTEND;VALUE=DATE-TIME:20240501T173000Z
DTSTAMP;VALUE=DATE-TIME:20240426T201246Z
ORGANIZER;CN=The Man:mailto:theman@myinviter.com
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;CN=me@there.com:mailto:me@there.com
UID:2gqc8j219jbeh97muvkte8bfl6@google.com
SUMMARY:2nd Interview with Keith Nordstrom - CTO
LOCATION:
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

    def test_simple_ical(self):
        event = message.Event.create(self.simple)
        assert event.event_id == '2gqc8j219jbeh97muvkte8bfl6@google.com'
        assert event.summary == '2nd Interview with Keith Nordstrom - CTO'
        assert event.location is None
        assert event.start.isoformat() == '2024-05-01T16:00:00+00:00'
        assert event.end.isoformat() == '2024-05-01T17:30:00+00:00'
        assert event.organizer.name == 'The Man'
        assert event.organizer.email == 'theman@myinviter.com'
        assert len(event.attendees) == 1
        assert event.attendees[0].name == 'me@there.com'
        assert event.attendees[0].email == 'me@there.com'

    complex = """BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VTIMEZONE
TZID:America/Denver
X-LIC-LOCATION:America/Denver
BEGIN:DAYLIGHT
TZOFFSETFROM:-0700
TZOFFSETTO:-0600
TZNAME:MDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0600
TZOFFSETTO:-0700
TZNAME:MST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTART;TZID=America/Denver:20240501T100000
DTEND;TZID=America/Denver:20240501T113000
DTSTAMP:20240426T200104Z
ORGANIZER;CN=The Man:mailto:org@recruiter.com
UID:2gqc8j219jbeh97muvkte8bfl6@google.com
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=
 TRUE;CN=me@there.com;X-NUM-GUESTS=0:mailto:me@there.com
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE
 ;CN=The Man;X-NUM-GUESTS=0:mailto:org@recruiter.com
ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=
 TRUE;CN=hiring@thecompany.com;X-NUM-GUESTS=0:mailto:hiring@thecompany.com
X-MICROSOFT-CDO-OWNERAPPTID:-1953847345
CREATED:20240426T200101Z
DESCRIPTION:
LAST-MODIFIED:20240426T200101Z
LOCATION:
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:2nd Interview with Keith Nordstrom - CTO
TRANSP:OPAQUE
ATTACH;FILENAME=KeithMichaelNordstrom_Resume-240315;FMTTYPE=application/vnd
 .google-apps.document:https://drive.google.com/open?id=1smztyFJ_SCG7R51MPfg
 HxaTroqZK9hqGEMFyNc7N-CM&authuser=0
ATTACH;FILENAME=Chief Technology Officer.docx;FMTTYPE=application/vnd.openx
 mlformats-officedocument.wordprocessingml.document:https://drive.google.com
 /open?id=1_4YI4mJKVyJHsdLjrs1hUJGhX_wnOkV9&authuser=0
END:VEVENT
END:VCALENDAR"""

    def test_complex_ical(self):
        event: message.Event = message.Event.create(self.complex)
        assert event.event_id == '2gqc8j219jbeh97muvkte8bfl6@google.com'
        assert event.summary == '2nd Interview with Keith Nordstrom - CTO'
        assert event.location is None
        assert event.start.isoformat() == '2024-05-01T10:00:00-06:00'
        assert event.end.isoformat() == '2024-05-01T11:30:00-06:00'
        assert event.organizer == EmailParticipant(name='The Man', email='org@recruiter.com')

        assert len(event.attendees) == 3
        assert MeetingAttendee(name='The Man', email='org@recruiter.com') in event.attendees
        assert MeetingAttendee(name='me@there.com', email='me@there.com') in event.attendees
        assert MeetingAttendee(name='hiring@thecompany.com', email='hiring@thecompany.com') in event.attendees