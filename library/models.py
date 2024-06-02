import datetime
import re
from base64 import urlsafe_b64decode
from typing import Union
from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
import icalendar
import ics
import recurring_ical_events
from library import utils, models
import ics

from library import utils, models
import re

class Message:

    @staticmethod
    def create_message(message: dict):
        return {
            "email_id": message.get('id'),
            "history_id": message.get('historyId'),
            "thread_id": message.get('threadId'),
            "labels": message.get('labelIds'),
            "date": str(datetime.datetime.fromtimestamp(int(message.get('internalDate')) / 1000)),
            "to": [],
            "cc": [],
            "bcc": [],
            "subject": None,
            "from": None,
            "body": ""
        }
    
    def clean_html(html):
        soup = BeautifulSoup(html, features="html.parser")
        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)# break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        #drop non-ascii unicode characters
        text = ''.join((c for c in str(text) if ord(c) < 128))
        return text
    
    def try_get_body(message: dict, new_message: dict):
        try:
            parts = message['payload']
            if parts.get("parts"):
                parts = parts['parts']
            else:
                parts = [parts]
            for part in parts:             
                if part['mimeType'] == 'text/plain':
                    new_message['body'] = EmailReplyParser.parse_reply(urlsafe_b64decode(part['body']['data']).decode('utf-8'))
                    break
                elif part['mimeType'] == 'text/html':
                    #other handling required?
                    new_message['body'] = EmailReplyParser.parse_reply(Message.clean_html(urlsafe_b64decode(part['body']['data']).decode('utf-8')))
                    break
        except KeyError:
            print("No parts found in message " + str(message) + " with payload " + str(message['payload']))
            pass

    @staticmethod
    def try_get_to(header: dict, new_message: dict):
        val = header['value']
        tos = val.split(',')
        for to in tos:
            try:
                name = to[:to.index('<')].strip()
                email = re.findall(r'(?<=<)(.*?)(?=>)', to)[0]
                new_message['to'].append({'name': name, 'email': email})
            except:
                new_message['to'].append({'name': None, 'email': to})

    @staticmethod
    def try_get_cc(header: dict, new_message: dict):
        val = header['value']
        tos = val.split(',')
        for to in tos:
            try:
                name = to[:to.index('<')].strip()
                email = re.findall(r'(?<=<)(.*?)(?=>)', to)[0]
                new_message['to'].append({'name': name, 'email': email})
            except:
                new_message['to'].append({'name': None, 'email': to})

    @staticmethod
    def try_get_bcc(header: dict, new_message: dict):
        val = header['value']
        tos = val.split(',')
        for to in tos:
            try:
                name = to[:to.index('<')].strip()
                email = re.findall(r'(?<=<)(.*?)(?=>)', to)[0]
                new_message['to'].append({'name': name, 'email': email})
            except:
                new_message['to'].append({'name': None, 'email': to})

    @staticmethod
    def try_get_from(header: dict, new_message: dict):
        val = header['value']
        try:
            name = val[:val.index('<')].strip()
            email = re.findall(r'(?<=<)(.*?)(?=>)', val)[0]

            new_message['from'] = {'email': email, 'name': name}
        except:
            new_message['from'] = val

    @staticmethod
    def try_get_attachments(message: dict, new_message: dict):
        attachments = message.get('attachments', [])
        events = []
        for attachment in attachments:
            filename = attachment['filename']
            if utils.Utils.is_invite(filename):
                try:  
                    original = urlsafe_b64decode(attachment['data']).decode('utf-8')
                    attachment['data'] = urlsafe_b64decode(attachment['data']).decode('utf-8')#EmailReplyParser.parse_reply()

                    # print()
                    # print("Attachment data", original)
                    # print()

                    event = models.Event.create(attachment['data'])
                    events.append(event)
                except Exception as e:
                    print("Error creating event from attachment " + str(attachment) + " with error ", e)

        if len(events) > 0:
            print("Events found in message " + str(events))
            new_message['events'] = events

    @staticmethod
    def extract_data(message: dict) -> dict:
        """
        takes a raw gmail message as a dictionary and returns the refactored version
        :param message: dict
        :return: dict
        """

        # get the data which can be taken directly from the raw message
        new_message = Message.create_message(message)

        Message.try_get_body(message, new_message)
        Message.try_get_attachments(message, new_message)      

        # check the headers to get the rest of the fields
        for header in message['payload']['headers']:
            # get name and emails of the recipients
            if header['name'] == 'To':
                Message.try_get_to(header, new_message)

            # get names and emails of cc
            if header['name'] == 'Cc':
                Message.try_get_cc(header, new_message)

            # get names and emails of bcc
            if header['name'] == 'Bcc':
                Message.try_get_bcc(header, new_message)

            #  get the subject
            if header['name'] == 'Subject':
                new_message['subject'] = header['value']

            # get the name and email of sender
            if header['name'] == 'From':
                Message.try_get_from(header, new_message)
                
        if new_message.get('from') and new_message.get('subject') and new_message.get('to') and new_message.get('date') and new_message.get('email_id') and new_message.get('history_id'):
            return new_message
        else:
            return None

class Event:

    @staticmethod
    def extract_person(component: Union[str,icalendar.vCalAddress]) -> dict:
        if not component:
            return None
        elif type(component) == str:
            email = component
            name = component
        else:
            email = component.to_ical().decode('utf-8')
            name = component.params.get('cn', '')

        email = email.replace('mailto:', '')                                                                  
        return {
            'name': name if name != '' else email,
            'email': email,
        }
    
    @staticmethod
    def extract_attendees(event: icalendar.Event) -> list:
        attendees = event.get('attendee')
        if attendees is None:
            attendees = []
        elif type(attendees) in [str, icalendar.vCalAddress]:
            attendees = [Event.extract_person(attendees)]
        else:
            attendees = [Event.extract_person(attendee) for attendee in event.get('attendee', [])]
        return attendees
    
    @staticmethod
    def create(file:str) -> dict:
        """Creates an event from an ics file using the icalendar library. Assumes a single event and returns the first if there are more"""

        events_also = icalendar.Calendar.from_ical(file)

        for event in recurring_ical_events.of(events_also).after(datetime.datetime.fromisoformat('19700101T00:00:00Z')):
            attendees = Event.extract_attendees(event)

            description = event.get('description', icalendar.vText(b'')).to_ical().decode('utf-8')
            summary = event.get('summary', icalendar.vText(b'')).to_ical().decode('utf-8')

            if description == '':
                description = summary
            elif summary == '':
                summary = description

            return {
                "event_id": event.get('uid').to_ical().decode('utf-8'),
                "summary": summary,
                "description": description,
                "location": event.get('location').to_ical().decode('utf-8') if event.get('location') else None,
                "start": event.get('dtstart').dt.isoformat(),
                "end": event.get('dtend').dt.isoformat(),
                "organizer": Event.extract_person(event.get('organizer')),
                "status": event.get('status').to_ical().decode('utf-8'),
                "attendees": attendees,
                "content": file
            }
            

    # @staticmethod
    # def create(file: str) -> dict:
    #     file = Event.repair_ics(file)
    #     events = ics.Calendar(file).events
        
    #         # print("Event name", event.get('name'))
    #         # print("Event description", event.get('description'), event.get('summary'))
    #         # print("Event location", event.get('location'))
    #         # print("Event begin", event.get('begin'), event.get('when'))
    #         # print("Event end", event.end)
    #         # print("Event organizer", event.organizer)
    #         # print("Event status", event.status)
    #         # print("Event attendees", event.attendees)

    #     for component in events:
    #         print("             Component", component)
    #         attendees = []
    #         for attendee in component.attendees: 
    #             attendees.append(Event.extract_person(attendee))

    #         print("Begin", component.begin)

    #         return {
    #             "event_id": component.uid,
    #             "summary": component.name,
    #             "description": component.description,
    #             "location": component.location,
    #             "start": str(component.begin),
    #             "end": str(component.end),
    #             "organizer": Event.extract_person(component.organizer),
    #             "status": component.status,
    #             "attendees": attendees,
    #             "content": file
    #         }