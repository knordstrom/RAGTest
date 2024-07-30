import datetime
import re
from base64 import urlsafe_b64decode
from typing import Union
from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
from pydantic import BaseModel, Field
from library import utils
import re

from library.models.event import Event
from library.weaviate_schemas import EmailParticipant

class Message(BaseModel):
    email_id: str
    history_id: str
    thread_id: str
    labels: list[str]
    date: datetime.datetime
    to: list[EmailParticipant]
    cc: list[EmailParticipant]
    bcc: list[EmailParticipant]
    subject: Union[str, None] = None
    from_: EmailParticipant
    body: str
    events: list[Event] = []

    class MessageHeaderData(BaseModel):
        to: list[EmailParticipant]
        cc: list[EmailParticipant] = Field(default = [])
        bcc: list[EmailParticipant] = Field(default = [])
        subject: str
        from_: EmailParticipant

    @staticmethod
    def from_gsuite_payload(message: dict[str, str]) -> 'Message':

        data: Message.MessageHeaderData = Message.extract_header_data(message)

        return Message(
            email_id = message.get('id'),
            history_id = message.get('historyId'),
            thread_id = message.get('threadId'),
            labels = message.get('labelIds'),
            date = datetime.datetime.fromtimestamp(int(message.get('internalDate')) / 1000).astimezone(),
            to = data.to,
            cc = data.cc,
            bcc = data.bcc,
            subject = data.subject,
            from_ = data.from_,
            body = Message.try_get_body(message),
            events = Message.try_get_attachments(message)
        )
    
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
    
    @staticmethod
    def try_get_body(message: dict[str, str]) -> str:
        try:
            parts = message['payload']
            if parts.get("parts"):
                parts = parts['parts']
            else:
                parts = [parts]
            for part in parts:             
                if part['mimeType'] == 'text/plain':
                    return EmailReplyParser.parse_reply(urlsafe_b64decode(part['body']['data']).decode('utf-8'))
                elif part['mimeType'] == 'text/html':
                    #other handling required?
                    return EmailReplyParser.parse_reply(Message.clean_html(urlsafe_b64decode(part['body']['data']).decode('utf-8')))
                
            return ""
        except KeyError:
            print("No parts found in message " + str(message) + " with payload " + str(message['payload']))
            return None

    @staticmethod
    def get_participant_list(header: dict[str, any]) -> list[EmailParticipant]:
        val = header['value']
        tos = val.split(',')
        result = []
        for to in tos:
            result.append(Message.get_participant(to))
        return result

    @staticmethod
    def try_get_from(header: dict[str, any]) -> EmailParticipant:
        val = header['value']
        return Message.get_participant(val)

    @staticmethod
    def get_participant(val: str) -> EmailParticipant:
        try:
            name = val[:val.index('<')].strip()
            email = re.findall(r'(?<=<)(.*?)(?=>)', val)[0]
            return EmailParticipant(email = email, name =  name)
        except:
            return EmailParticipant(email = val, name = val)

    @staticmethod
    def try_get_attachments(message: dict) -> list[Event]:
        attachments = message.get('attachments', [])
        events: list[Event] = []
        for attachment in attachments:
            filename = attachment['filename']
            if utils.Utils.is_invite(filename):
                try:  
                    original = urlsafe_b64decode(attachment['data']).decode('utf-8')
                    attachment['data'] = urlsafe_b64decode(attachment['data']).decode('utf-8')
                    event = Event.create(attachment['data'])
                    events.append(event)
                except Exception as e:
                    print("Error creating event from attachment " + str(attachment) + " with error ", e)

        if len(events) > 0:
            print("Events found in message " + str(events))
        return events

    @staticmethod
    def extract_header_data(message: dict[str, any]) -> 'Message.MessageHeaderData':
        """
        takes a raw gmail message as a dictionary and returns the refactored version
        :param message: dict
        :return: Message.MessageHeaderData
        """
        result: dict[str, any] = {
            'to': [],
            'cc': [],
            'bcc': [],
            'subject': None,
            'from_': None,
        }

        # check the headers to get the rest of the fields
        for header in message['payload']['headers']:
            # get name and emails of the recipients
            if header['name'] == 'To':
                result['to'] = Message.get_participant_list(header)

            # get names and emails of cc
            if header['name'] == 'Cc':
                result['cc'] = Message.get_participant_list(header)

            # get names and emails of bcc
            if header['name'] == 'Bcc':
                result['bcc'] = Message.get_participant_list(header)

            #  get the subject
            if header['name'] == 'Subject':
                result['subject'] = header['value']

            # get the name and email of sender
            if header['name'] == 'From':
                result['from_'] = Message.try_get_from(header)
                
        return Message.MessageHeaderData.model_validate(result)

