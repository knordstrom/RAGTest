
from datetime import datetime
import os
from collections import defaultdict
from library.data.local import weaviate
from library.models.api_models import BriefContext, BriefResponse, DocumentEntry, DocumentMetadata, EmailConversationEntry, MeetingAttendee, MeetingContext, MeetingSupport, SlackConversationEntry, SlackThreadResponse, TranscriptConversation, TranscriptEntry
from library.managers.importance import ImportanceService

from library.managers.briefing_summarizer import BriefingSummarizer
from library.models.event import Event
import library.data.local.neo4j as neo
from dotenv import load_dotenv
from library.llms.promptmanager import PromptManager
from library.utils import Utils
from library.models.weaviate_schemas import Email, EmailConversationWithSummary, EmailParticipant, EmailText, EmailTextWithFrom, WeaviateSchemas
from weaviate.collections.classes.internal import Object

class BriefingSupport:

    prompt_manager: PromptManager = PromptManager()
    weave: weaviate.Weaviate = weaviate.Weaviate()
    summarizer: BriefingSummarizer

    def __init__(self, summarizer: BriefingSummarizer) -> None:
        self.summarizer: BriefingSummarizer = summarizer

    def create_briefings_for_summary(self, email: str, start_time: datetime, end_time: datetime, schedule: list[dict]) -> str:
        out = self.summarizer.summarize('BriefingSupport.create_briefings_for', {
            'email': email,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'Context': str(schedule)
        })
        return out

    def create_briefings_for(self, email: str, start_time: datetime, end_time: datetime, certainty: float = None, threshold: float = None, use_hyde: bool = False) -> BriefResponse:
        """    # retrieve person node from neo4j
        #    retrieve associated people
        #    retrieve associated events
        # rerieve email chains that are
        #    1. associated with the person
        #    2. pertinent to the events"""
        load_dotenv()
        print("Getting schedule for " + email + " from " + start_time.isoformat() + " to " + end_time.isoformat())   
        n = neo.Neo4j()
        schedule: list[Event] = n.get_schedule(email, start_time, end_time)
        print("Schedule was ", schedule)

        summary: str = self.create_briefings_for_summary(email, start_time, end_time, schedule)
        importanceService = ImportanceService()
        meetings = []
        for event in schedule:
            support = self.contextualize(event, certainty, threshold = threshold, use_hyde = use_hyde)
            attendees = event.attendees
            organizer = MeetingAttendee(name = event.organizer.name, email = event.organizer.email) if event.organizer else None
            meeting = MeetingContext(attendees=attendees, start=event.start, end=event.end, description=event.description, 
                                     recurring_id = event.recurring_id, name=event.summary, person = MeetingAttendee(name = email, email = email), 
                                     organizer=organizer, support=support)
            importanceService.add_importance_to_meeting(meeting)
            meetings.append(meeting)
     
        return BriefResponse(email=email, start_time=start_time, end_time=end_time, summary=summary, context=BriefContext(schedule = meetings))
     
    def contextualize(self, event: Event, certainty: float = None, threshold: float = None, use_hyde: bool = False) -> MeetingSupport:
        sum_docs: list[DocumentEntry] = self.doc_context_for(event, certainty, threshold=threshold, use_hyde = use_hyde)
        sum_email: list[EmailConversationEntry] = self.email_context_for(event, certainty, threshold=threshold, use_hyde = use_hyde)
        sum_slack: list[SlackConversationEntry] = self.slack_context_for(event, certainty, threshold=threshold, use_hyde = use_hyde)
        sum_transcripts: list[TranscriptEntry] = self.transcript_context_for(event, certainty, threshold=threshold, use_hyde = use_hyde)

        return MeetingSupport(
            docs=sum_docs,
            email=sum_email,
            slack=sum_slack,
            calls=sum_transcripts
        )
    
    def doc_context_for(self, event: Event, certainty: float = None, threshold: float = None, use_hyde: bool = False) -> list[DocumentEntry]:
        sum_docs = self.context_for(event, WeaviateSchemas.DOCUMENT_SUMMARY, WeaviateSchemas.DOCUMENT, 'document_id', certainty, threshold, use_hyde)
        response = []
        for doc in sum_docs:
            response.append(DocumentEntry(
                    document_id = doc['document_id'],
                    doc_type = doc['doc_type'], 
                    metadata = DocumentMetadata(
                        created_time =  doc['metadata']['createdTime'],
                        metadata_id =  doc['metadata']['metadata_id'],
                        modified_time =  doc['metadata']['modifiedTime'],
                        mime_type =  doc['metadata']['mimeType'],
                        name =  doc['metadata']['name'],
                        last_response =  doc['metadata']['modifiedTime'],
                    ),
                    provider = doc.get('provider'),
                    summary = doc['text'],
            ))
        return response

    def construct_conversation_and_summary(self, emails_dict: dict[str, list[EmailTextWithFrom]]) -> dict[str,EmailConversationWithSummary]:
        thread_id:str
        emails:list[EmailTextWithFrom]
        details: EmailTextWithFrom
        response: dict[str, EmailConversationWithSummary] = {}
        for thread_id, emails in emails_dict.items():
            conversation = ""
            if len(emails) == 0:
                continue
            for details in emails:
                sender_name = details.sender.name
                text = details.text
                conversation += f"\n{sender_name}: {text}"
            conversation_summary = self.summarizer.summarize('Summarizer.email_summarizer', {'Conversation': conversation})
            response[thread_id] = EmailConversationWithSummary(thread_id= thread_id, conversation=conversation, summary=conversation_summary,
                                                               last_response=emails[-1].date)
        return response

    def get_thread_email_message_by_id(self, thread_ids: list[str], email_map: dict[str, Email]) -> dict[str,list[EmailTextWithFrom]]:
        w = self.weave
        threads: dict[str, list[EmailTextWithFrom]] = {}
        for thread in thread_ids:
            email_texts_using_thread_id: list[EmailText] = w.get_thread_email_messages_by_id(thread)
            if thread not in threads:
                threads[thread] = []

            for email_text in email_texts_using_thread_id:
                email_id = email_text.email_id
                if email_map.get(email_id):
                    sender = email_map.get(email_id).sender
                    m = email_text.model_dump()
                    m['sender'] = sender
                    threads[thread].append(EmailTextWithFrom(**m))
        return threads

    def collate_email_messages_by_thread_id(self, emails: list[EmailTextWithFrom]) -> EmailTextWithFrom:
        text: list[str] = []
        for email in emails:
            text.append(email.text)
        return EmailTextWithFrom(email_id=emails[0].email_id, thread_id=emails[0].thread_id, ordinal=emails[0].ordinal, 
                                 text=" ".join(text), sender=emails[0].sender)

    def group_messages_by_thread_id(self, threads: dict[str,list[EmailTextWithFrom]]) -> dict[str, list[EmailTextWithFrom]]:
        grouped_messages: dict[str, list[EmailTextWithFrom]] = {}

        thread_id: str
        messages: list[EmailTextWithFrom]
        message: EmailTextWithFrom
        for thread_id, messages in threads.items():
            grouped_messages[thread_id] = {}
            for message in messages:
                email_id: str= message.email_id
                
                if email_id not in grouped_messages[thread_id]:
                    grouped_messages[thread_id][email_id] = []
                grouped_messages[thread_id][email_id].append(message)

            for email_id in grouped_messages[thread_id]:
                grouped_messages[thread_id][email_id] = self.collate_email_messages_by_thread_id(grouped_messages[thread_id][email_id])

            for thread_id, messages in threads.items():
                grouped_messages[thread_id] = sorted(messages, key=lambda x: x.ordinal)

        return grouped_messages
    
    def get_thread_emails(self, sum_email: list[dict[str, any]]) -> dict[str, list[EmailTextWithFrom]]:
        thread_text: dict[str, list[EmailTextWithFrom]] = {}
        w = self.weave
        for email_dict in sum_email:
            thread_id = email_dict['thread_id']
            if thread_id not in thread_text:
                thread_list: list[EmailTextWithFrom] = w.get_thread_email_messages_by_id(thread_id)
                thread_text[thread_id] = thread_list
        return thread_text
    
    def email_context_for(self, event: Event, certainty: float = None, threshold: float = None, use_hyde: bool = False) -> list[EmailConversationEntry]:
        sum_email: list[dict[str, any]] = self.context_for(event, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'email_id', 
                                                           certainty, threshold=threshold, use_hyde = use_hyde) 
        email_thread: dict[str, list[EmailTextWithFrom]] = self.get_thread_emails(sum_email) 
        return self.process_email_context(email_thread)
  
    def process_email_context(self, threads: dict[str, list[EmailTextWithFrom]])-> list[EmailConversationEntry]:
        summarized_conversations: dict[str,EmailConversationWithSummary] = self.construct_conversation_and_summary(threads)
        result: list[EmailConversationEntry] = []
        for conversation in summarized_conversations.values():
            result.append(EmailConversationEntry(
                text = conversation.conversation,
                thread_id = conversation.thread_id, 
                summary = conversation.summary,
                last_response = conversation.last_response,
            ))

        return result
    
    def slack_context_for(self, event: Event, certainty: float = None, threshold: float = None, use_hyde: bool = False) -> list[SlackConversationEntry]:
        sum_slack = self.context_for(event, WeaviateSchemas.SLACK_MESSAGE_TEXT, WeaviateSchemas.SLACK_THREAD, 'thread_id', 
                                     certainty, threshold= threshold, use_hyde = use_hyde)
        prompt = self.prompt_manager.get_latest_prompt_template("BriefingSupport.slack_context_for")
        w = self.weave
        result: list[SlackConversationEntry] = []
        for thread in sum_slack:
            messages: SlackThreadResponse = w.get_slack_thread_messages_by_id(thread['thread_id'])
            conversation = ""
            for message in messages.messages:
                conversation += "\n" + message.sender + ": " + "".join(message.text)
            
            summary = self.summarizer.summarize_with_prompt(prompt, {'Conversation': conversation})
            result.append(SlackConversationEntry(
                text = conversation,
                thread_id = thread['thread_id'],
                channel_id = thread['channel_id'],
                summary = summary,
                last_response = messages.messages[-1].ts
            ))
        return result
    
    def transcript_context_for(self, event: Event, certainty: float, threshold: float, use_hyde: bool = False) -> list[TranscriptEntry]:
        sum_transcript = self.context_for(event, WeaviateSchemas.TRANSCRIPT_ENTRY, WeaviateSchemas.TRANSCRIPT, 'meeting_code', certainty, threshold,  use_hyde)
        prompt = self.prompt_manager.get_latest_prompt_template("BriefingSupport.transcript_context_for")
        w = self.weave
        result: list[TranscriptEntry] = []
        for transcript in sum_transcript:
            record: TranscriptConversation = w.get_transcript_conversation_by_meeting_code(transcript['meeting_code'])
            conversation = ""
            for message in record.conversation:
                conversation += "\n" + message.speaker + ": " + "".join(message.text)
            
            summary = self.summarizer.summarize_with_prompt(prompt, {'Conversation': conversation})
            result.append(TranscriptEntry(
                document_id = record.transcript_id,
                meeting_code = record.meeting_code,
                provider = record.provider,
                title = record.title,
                attendee_names = record.attendee_names,
                summary= summary
            ))
        return result
    
    def context_for(self, event: Event, source: WeaviateSchemas, meta_source: WeaviateSchemas, id_prop: str, 
                    certainty: float = None, threshold: float = None, use_hyde: bool = False) -> list[dict[str, any]]:
        w = self.weave
        cv = .3 if not certainty else certainty
        th = .3 if not threshold else threshold
        print(event)
        res: list[Object[any,any]] = w.search(event.summary, source, certainty = cv, threshold = threshold, use_hyde = use_hyde)
        dsc_res: list[Object[any,any]] = w.search(event.description, source, certainty = cv, threshold = threshold, use_hyde = use_hyde) if event.description!= None and event.description!= '' else []
        res.extend(dsc_res)
        result: dict[str, any] = {}
        for o in res:
            props = o.properties
            result[props[id_prop]] = props        

        ids = list(result.keys())
        if len(ids) > 0:
            meta_res: list[Object[any, any]] = w.get_by_ids(meta_source, id_prop, ids)
            for o in meta_res:
                print("Updating result with key", o.properties[id_prop], "with ", o.properties)
                result.get(o.properties[id_prop], {}).update(o.properties)

        return list(result.values())


