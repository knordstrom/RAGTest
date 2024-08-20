import datetime
from base64 import urlsafe_b64decode
from typing import Union
import icalendar
import ics
from pydantic import BaseModel
import recurring_ical_events
import ics

from library.models.api_models import MeetingAttendee
from library.models.weaviate_schemas import EmailParticipant

class Event(BaseModel):
    event_id: str
    summary: Union[str, None] = None
    description: Union[str, None] = None
    location: Union[str, None] = None
    start: datetime.datetime
    end: datetime.datetime
    organizer: Union[EmailParticipant, None] = None 
    status: Union[str, None] = None
    attendees: list[MeetingAttendee]
    content: Union[str, None] = None
    recurring_id: Union[str, None] = None

    @staticmethod
    def extract_person(component: Union[str,icalendar.vCalAddress]) -> EmailParticipant:
        if not component:
            return None
        elif type(component) == str:
            email = component
            name = component
        else:
            email = component.to_ical().decode('utf-8')
            name = component.params.get('cn', '')

        email = email.replace('mailto:', '')                                                                  
        return EmailParticipant(
            name =  name if name != '' else email,
            email =  email,
        )
    
    @staticmethod
    def extract_attendees(event: icalendar.Event) -> list[MeetingAttendee]:
        attendees: list[MeetingAttendee] = event.get('attendee', [])
        if type(attendees) in [str, icalendar.vCalAddress]:
            att = [Event.extract_person(attendees)]
            attendees = [MeetingAttendee(email = a.email, name = a.name) for a in att]
        else:
            att = [Event.extract_person(attendee) for attendee in attendees]
            attendees = [MeetingAttendee(email = a.email, name = a.name) for a in att]
        return attendees
    
    @staticmethod
    def create(file:str) -> 'Event':
        """Creates an event from an ics file using the icalendar library. Assumes a single event and returns the first if there are more"""

        events_also = icalendar.Calendar.from_ical(file)

        for event in recurring_ical_events.of(events_also).after(datetime.datetime.fromisoformat('19700101T00:00:00Z')):
            attendees: list[MeetingAttendee] = Event.extract_attendees(event)

            description = event.get('description', icalendar.vText(b'')).to_ical().decode('utf-8')
            summary = event.get('summary', icalendar.vText(b'')).to_ical().decode('utf-8')

            if description == '':
                description = summary
            elif summary == '':
                summary = description

            return Event(               
                event_id = event.get('uid').to_ical().decode('utf-8'),
                summary =  summary,
                description =  description,
                location =  event.get('location').to_ical().decode('utf-8') if event.get('location') else None,
                start =  event.get('dtstart').dt.isoformat(),
                end =  event.get('dtend').dt.isoformat(),
                organizer =  Event.extract_person(event.get('organizer')),
                status =  event.get('status').to_ical().decode('utf-8'),
                attendees =  attendees,
                recurring_id = event.get('recurrence-id').to_ical().decode('utf-8') if event.get('recurrence-id') else None,
                content =  file
            )