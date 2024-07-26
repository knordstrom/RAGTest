
from datetime import datetime
import os
from collections import defaultdict
from library import weaviate
from library.api_models import BriefContext, BriefResponse, DocumentEntry, EmailConversationEntry, MeetingAttendee, MeetingContext, MeetingSupport, SlackConversationEntry, SlackThreadResponse
from library.groq_client import GroqClient
from library.models.event import Event
import library.neo4j as neo
from dotenv import load_dotenv
from library.promptmanager import PromptManager
from library.utils import Utils
from library.weaviate_schemas import Email, EmailConversationWithSummary, EmailParticipant, EmailText, EmailTextWithFrom, WeaviateSchemas
from weaviate.collections.classes.internal import Object


class BriefingSupport:

    @staticmethod
    def create_briefings_for_summary(email: str, start_time: datetime, end_time: datetime, schedule: list[dict]) -> str:
        prompt = PromptManager().get_latest_prompt_template('APISupport.create_briefings_for')  
        return GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=2000).query(prompt, {
            'email': email,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'Context': str(schedule)
        })

    @staticmethod
    def create_briefings_for(email: str, start_time: datetime, end_time: datetime, certainty: float = None) -> BriefResponse:
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

        summary: str = BriefingSupport.create_briefings_for_summary(email, start_time, end_time, schedule)
        
        meetings = []
        for event in schedule:
            support = BriefingSupport.contextualize(event, certainty)
            attendees = event.attendees
            organizer = MeetingAttendee(name = event.organizer.name, email = event.organizer.email) if event.organizer else None
            meeting = MeetingContext(attendees=attendees, start=event.start, end=event.end, description=event.description, 
                                     recurring_id = event.recurring_id, name=event.summary, person = MeetingAttendee(name = email, email = email), 
                                     organizer=organizer, support=support)
            meetings.append(meeting)
     
        return BriefResponse(email=email, start_time=start_time, end_time=end_time, summary=summary, context=BriefContext(schedule = meetings))
     
    @staticmethod
    def contextualize(event: Event, certainty: float = None) -> MeetingSupport:
        sum_docs: list[DocumentEntry] = BriefingSupport.doc_context_for(event, certainty)
        sum_email: list[EmailConversationEntry] = BriefingSupport.email_context_for(event, certainty)
        sum_slack: list[SlackConversationEntry] = BriefingSupport.slack_context_for(event, certainty)

        return MeetingSupport(
            docs=sum_docs,
            email=sum_email,
            slack=sum_slack
        )
    
    @staticmethod
    def doc_context_for(event: Event, certainty: float = None) -> list[DocumentEntry]:
        sum_docs = BriefingSupport.context_for(event, WeaviateSchemas.DOCUMENT_SUMMARY, WeaviateSchemas.DOCUMENT, 'document_id', certainty)
        Utils.remove_keys([['metadata', 'lastModifyingUser'],['metadata', 'owners'],['metadata', 'permissions']], sum_docs)
        response = []
        for doc in sum_docs:
            Utils.rename_key(doc, 'text', 'summary')
            response.append(DocumentEntry.model_validate(doc))
        return response

    @staticmethod
    def construct_conversation_and_summary(emails_dict: dict[str, list[EmailTextWithFrom]]) -> dict[str,EmailConversationWithSummary]:
        # prompt = """
        #     Below is a series of email conversations between different individuals. Please read through the conversations and provide a concise summary that captures the main points and key takeaways from these exchanges.

        #     Conversations:
        #     {Conversation}

        #     Please summarize the conversations, highlighting any important decisions, action items, and key topics discussed.
        #     """
        mgr: PromptManager = PromptManager()
        prompt = mgr.get_latest_prompt_template('Summarizer.email_summarizer')

        thread_id:str
        emails:list[EmailTextWithFrom]
        details: EmailTextWithFrom

        response: dict[str, EmailConversationWithSummary] = {}
        for thread_id, emails in emails_dict.items():
            for details in emails:
                conversation = ""
                sender_name = details.from_
                text = details.text
                conversation += f"\n{sender_name}: {text}"
            conversation_summary = GroqClient(os.getenv('GROQ_API_KEY')).query(prompt, {'Conversation': conversation})
            print("Summary: ", conversation_summary)
            response[thread_id] = EmailConversationWithSummary(thread_id= thread_id, conversation=conversation, summary=conversation_summary)
        return response

    @staticmethod
    def get_email_thread_ids(emails: list[dict[str, any]]) -> tuple[list[str], list[str]]:
        thread_ids: dict[str, str] = {}
        email_ids: dict[str, str] = {}
        for email in emails:
            thread_ids[email["thread_id"]] = email["thread_id"]
            email_ids[email["email_id"]] = email["email_id"]
        return list(thread_ids.keys()), list(email_ids.keys())
    
    @staticmethod
    def get_email_metadata(email_ids: list[str]) -> dict[str, Email]:
        w: weaviate.Weaviate = weaviate.Weaviate()
        email_metadata = {}
        for email in email_ids:
            email_metadata_using_email_id: Email = w.get_email_metadata_by_id(email)
            email_metadata[email] = email_metadata_using_email_id
        return email_metadata

    @staticmethod
    def get_thread_email_message_by_id(thread_ids: list[str], email_map: dict[str, Email]) -> dict[str,list[EmailTextWithFrom]]:
        w: weaviate.Weaviate = weaviate.Weaviate()
        threads: dict[str, list[EmailTextWithFrom]] = {}
        for thread in thread_ids:
            email_texts_using_thread_id: list[EmailText] = w.get_thread_email_messages_by_id(thread)
            if thread not in threads:
                threads[thread] = []

            for email_text in email_texts_using_thread_id:
                email_id = email_text.email_id
                if email_map.get(email_id):
                    from_ = email_map.get(email_id).from_
                    m = email_text.model_dump()
                    m['from_'] = from_
                    threads[thread].append(EmailTextWithFrom(**m))
        return threads

    @staticmethod
    def collate_email_messages_by_thread_id(emails: list[EmailTextWithFrom]) -> EmailTextWithFrom:
        text: list[str] = []
        for email in emails:
            text.append(email.text)
        return EmailTextWithFrom(email_id=emails[0].email_id, thread_id=emails[0].thread_id, ordinal=emails[0].ordinal, 
                                 text=" ".join(text), from_=emails[0].from_)

    @staticmethod
    def group_messages_by_thread_id_email_id(threads: dict[str,list[EmailTextWithFrom]]) -> dict[str, list[EmailTextWithFrom]]:
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
                grouped_messages[thread_id][email_id] = BriefingSupport.collate_email_messages_by_thread_id(grouped_messages[thread_id][email_id])

            for thread_id, messages in threads.items():
                grouped_messages[thread_id] = sorted(messages, key=lambda x: x.ordinal)

        return grouped_messages
    
    @staticmethod
    def email_context_for(event: Event, certainty: float = None) -> list[EmailConversationEntry]:
        sum_email: list[dict[str, any]] = BriefingSupport.context_for(event, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'email_id', certainty)

        thread_ids, email_ids = BriefingSupport.get_email_thread_ids(sum_email)
        email_metadata: dict[str, Email] = BriefingSupport.get_email_metadata(email_ids)
        threads: dict[str,list[EmailTextWithFrom]] = BriefingSupport.get_thread_email_message_by_id(thread_ids, email_metadata)

        conversations: dict[str, list[EmailTextWithFrom]] = BriefingSupport.group_messages_by_thread_id_email_id(threads)
        summarized_conversations: dict[str,EmailConversationWithSummary] = BriefingSupport.construct_conversation_and_summary(conversations)

        result: list[EmailConversationEntry] = []
        for conversation in summarized_conversations.values():
            result.append(EmailConversationEntry(text = conversation.conversation,
                thread_id = conversation.thread_id, 
                summary = conversation.summary))

        return result
    
    @staticmethod
    def slack_context_for(event: Event, certainty: float = None) -> list[SlackConversationEntry]:
        sum_slack = BriefingSupport.context_for(event, WeaviateSchemas.SLACK_MESSAGE_TEXT, WeaviateSchemas.SLACK_THREAD, 'thread_id', certainty)
        prompt = """Please summarize the following conversation in a few sentences.
        
        {Conversation}"""
        w = weaviate.Weaviate()
        result: list[SlackConversationEntry] = []
        for thread in sum_slack:
            messages: SlackThreadResponse = w.get_slack_thread_messages_by_id(thread['thread_id'])
            messages: SlackThreadResponse = w.get_slack_thread_messages_by_id(thread['thread_id'])
            conversation = ""
            for message in messages.messages:
                conversation += "\n" + message.sender + ": " + "".join(message.text)
            for message in messages.messages:
                conversation += "\n" + message.sender + ": " + "".join(message.text)
            
            thread['text'] = conversation
            thread['summary'] = GroqClient(os.getenv('GROQ_API_KEY')).query(prompt, {'Conversation': conversation})
            result.append(SlackConversationEntry.model_validate(thread))
        return result
    
    @staticmethod
    def context_for(event: Event, source: WeaviateSchemas, meta_source: WeaviateSchemas, id_prop: str, certainty: float = None) -> list[dict[str, any]]:
        w: weaviate.Weaviate = weaviate.Weaviate()
        cv = .3 if not certainty else certainty
        print(event)
        res: list[object] = w.search(event.summary, source, certainty = cv)
        dsc_res: list[object] = w.search(event.description, source) if event.description!= None and event.description!= '' else []
        result: dict[str, any] = {}
        for o in res:
            props = o.properties
            result[props[id_prop]] = props
        for o in dsc_res:
            props = o.properties
            result[props[id_prop]] = props

        ids = list(result.keys())
        if len(ids) > 0:
            meta_res: list[Object[any, any]] = w.get_by_ids(meta_source, id_prop, ids)
            for o in meta_res:
                print("Updating result with key", o.properties[id_prop], "with ", o.properties)
                result.get(o.properties[id_prop], {}).update(o.properties)

        return list(result.values())
