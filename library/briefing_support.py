
from datetime import datetime
import os
from collections import defaultdict
from library import weaviate
from library.groq_client import GroqClient
import library.neo4j as neo
from dotenv import load_dotenv
from library.promptmanager import PromptManager
from library.utils import Utils
from library.weaviate_schemas import WeaviateSchemas



class BriefingSupport:

    @staticmethod
    def create_briefings_for(email: str, start_time: datetime, end_time: datetime, certainty: float = None) -> dict:
        """    # retrieve person node from neo4j
        #    retrieve associated people
        #    retrieve associated events
        # rerieve email chains that are
        #    1. associated with the person
        #    2. pertinent to the events"""

        n = neo.Neo4j()
        n.connect()

        print("Getting schedule for " + email + " from " + start_time.isoformat() + " to " + end_time.isoformat())
        schedule = n.get_schedule(email, start_time, end_time)
        print("Schedule was ", schedule)

        prompt = PromptManager().get_latest_prompt_template('APISupport.create_briefings_for')
        print("Briefing prompt is ", prompt)

        context = {
            'email': email,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'Context': str(schedule)
        }

        load_dotenv()

        chat_completion = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=2000).query(prompt, context)
        for event in schedule:
            event['support'] = BriefingSupport.contextualize(event, certainty)

        context.update({
            'summary': chat_completion,
            'context': {
                'schedule': schedule
            },
        })
        del context['Context']          
        return context
    
    @staticmethod
    def contextualize(event: dict, certainty: float = None) -> dict:
        sum_docs = BriefingSupport.doc_context_for(event, certainty)
        sum_email = BriefingSupport.email_context_for(event, certainty)
        sum_slack = BriefingSupport.slack_context_for(event, certainty)

        return {
                'docs': sum_docs,
                'email': sum_email,
                'slack': sum_slack
            }

    # @staticmethod
    # def get_email_thread_context(event: dict, certainty: float = None) -> list[dict]:

    
    @staticmethod
    def doc_context_for(event: dict, certainty: float = None) -> list[dict]:
        sum_docs = BriefingSupport.context_for(event, WeaviateSchemas.DOCUMENT_SUMMARY, WeaviateSchemas.DOCUMENT, 'document_id', certainty)
        Utils.remove_keys([['metadata', 'lastModifyingUser'],['metadata', 'owners'],['metadata', 'permissions']], sum_docs)
        for doc in sum_docs:
            Utils.rename_key(doc, 'text', 'summary')
        return sum_docs

    
    @staticmethod
    def find_sender_by_email_id(email_id, data_list):
        """
        Find the 'from' field in dictionaries within a list where 'email_id' matches the given email_id.

        :param email_id: The email_id to search for.
        :param data_list: List of dictionaries, each containing an 'email_id' and 'from' field.
        :return: The 'from' field of the matching dictionary or None if no match is found.
        """
        filtered_data = list(filter(lambda x: x['email_id'] == email_id, data_list))
        if filtered_data:
            head = filtered_data[0]  # Get the first item
            result = head['from']
        else:
            result = None
        return result

    @staticmethod
    def construct_conversation_and_summary(emails_dict: dict) -> dict:
        prompt = """
            Below is a series of email conversations between different individuals. Please read through the conversations and provide a concise summary that captures the main points and key takeaways from these exchanges.

            Conversations:
            {Conversation}

            Please summarize the conversations, highlighting any important decisions, action items, and key topics discussed.
            """
        for thread_id, emails in emails_dict.items():
            for email_id, details in emails.items():
                conversation = ""
                sender_name = details['from']['name'] if details['from'] else "Unknown"
                text = details['text']
                conversation += f"\n{sender_name}: {text}"
            conversation_summary = GroqClient(os.getenv('GROQ_API_KEY')).query(prompt, {'Conversation': conversation})
            print("Summary: ", conversation_summary)
            emails_dict[thread_id]['summary'] = conversation_summary
        return emails_dict

    @staticmethod
    def add_unique_item(item, item_list):
        if item not in item_list:
            item_list.append(item)

    @staticmethod
    def get_email_thread_ids(emails: list[dict]) -> tuple[list, list]:
        thread_ids = []
        email_ids = []
        for email in emails:
            # Add the thread_id to the list if it's not already present
            BriefingSupport.add_unique_item(email["thread_id"], thread_ids)
            # Add the email_id to the list if it's not already present
            BriefingSupport.add_unique_item(email["email_id"], email_ids)
        return thread_ids, email_ids
    
    @staticmethod
    def get_email_metadata(email_ids: list[str]) -> list[dict]:
        w = weaviate.Weaviate()
        email_metadata = []
        for email in email_ids:
            email_metadata_using_email_id = w.get_email_metadata(email)
            if email_metadata_using_email_id:
                for item in email_metadata_using_email_id:
                    email_metadata.append(item)
        return email_metadata

    @staticmethod
    def get_thread_email_message_by_id(thread_ids: list) -> dict:
        w = weaviate.Weaviate()
        threads = {}
        for thread in thread_ids:
            email_texts_using_thread_id = w.get_thread_email_message_by_id(thread)
            if thread in threads:
                threads[thread].extend(email_texts_using_thread_id)
            else:
                threads[thread] = email_texts_using_thread_id
        # Dictionary to hold the combined results
        return threads

    @staticmethod
    def group_messages_by_thread_id(threads: dict) -> dict:
        grouped_messages = {}

        # Group and order messages by email_id and ordinal
        for thread_id, messages in threads.items():
            grouped_messages[thread_id] = {}
            for message in messages:
                email_id = message['email_id']
                ordinal = message['ordinal']
                text = message['text']
                if email_id not in grouped_messages[thread_id]:
                    grouped_messages[thread_id][email_id] = []
                grouped_messages[thread_id][email_id].append((ordinal, text))

        return grouped_messages

    @staticmethod
    def order_messages_and_add_sender_to_text(grouped_messages: defaultdict, email_metadata: list) -> defaultdict:
        # Sort texts by ordinal and combine them
        for thread_id in grouped_messages:
            for email_id in grouped_messages[thread_id]:
                sorted_texts = sorted(grouped_messages[thread_id][email_id], key=lambda x: x[0])  # Sort by ordinal
                grouped_messages[thread_id][email_id] = ' '.join(text for _, text in sorted_texts)

        
        for key, inner_dict in grouped_messages.items():
            for sub_key, text in inner_dict.items():
                grouped_messages[key][sub_key] = {'text': text, 'from': BriefingSupport.find_sender_by_email_id(sub_key, email_metadata)}
        return grouped_messages
    @staticmethod
    def email_context_for(event: dict, certainty: float = None) -> list[dict]:
        sum_email = BriefingSupport.context_for(event, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'email_id', certainty)
        w = weaviate.Weaviate()
        thread_ids, email_ids = BriefingSupport.get_email_thread_ids(sum_email)
        email_metadata = BriefingSupport.get_email_metadata(email_ids)
        threads = BriefingSupport.get_thread_email_message_by_id(thread_ids)
        grouped_messages = BriefingSupport.group_messages_by_thread_id(threads)
        grouped_messages = BriefingSupport.order_messages_and_add_sender_to_text(grouped_messages, email_metadata)
        grouped_messages = BriefingSupport.construct_conversation_and_summary(grouped_messages)
        for email in sum_email:
            email['summary'] = "N/A" if email['thread_id'] not in grouped_messages else grouped_messages[email['thread_id']]['summary']
        return sum_email

    
    @staticmethod
    def slack_context_for(event: dict, certainty: float = None) -> list[dict]:
        sum_slack = BriefingSupport.context_for(event, WeaviateSchemas.SLACK_MESSAGE_TEXT, WeaviateSchemas.SLACK_THREAD, 'thread_id', certainty)
        prompt = """Please summarize the following conversation in a few sentences.
        
        {Conversation}"""
        w = weaviate.Weaviate()
        for thread in sum_slack:
            messages = w.get_slack_thread_messages_by_id(thread['thread_id'])
            conversation = ""
            for message in messages['messages']:
                conversation += "\n" + message['from'] + ": " + message['text']
            
            thread['text'] = conversation
            thread['summary'] = GroqClient(os.getenv('GROQ_API_KEY')).query(prompt, {'Conversation': conversation})
        return sum_slack
    
    @staticmethod
    def context_for(event: dict, source: WeaviateSchemas, meta_source: WeaviateSchemas, id_prop: str, certainty: float = None) -> list[dict]:
        w = weaviate.Weaviate()
        cv = .3 if not certainty else certainty
        res = w.search(event['name'], source, certainty = cv).objects
        dsc_res = w.search(event['description'], source).objects if not event.get('description', '') == '' else []
        result = {}
        for o in res:
            props = o.properties
            result[props[id_prop]] = props
        for o in dsc_res:
            props = o.properties
            result[props[id_prop]] = props

        ids = list(result.keys())
        if len(ids) > 0:
            meta_res = w.get_by_ids(meta_source, id_prop, ids).objects
            for o in meta_res:
                print("Updating result with key", o.properties[id_prop], "with ", o.properties)
                result.get(o.properties[id_prop], {}).update(o.properties)

        return list(result.values())
