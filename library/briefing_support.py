
from datetime import datetime
import os
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
    
    @staticmethod
    def doc_context_for(event: dict, certainty: float = None) -> list[dict]:
        sum_docs = BriefingSupport.context_for(event, WeaviateSchemas.DOCUMENT_SUMMARY, WeaviateSchemas.DOCUMENT, 'document_id', certainty)
        Utils.remove_keys([['metadata', 'lastModifyingUser'],['metadata', 'owners'],['metadata', 'permissions']], sum_docs)
        for doc in sum_docs:
            Utils.rename_key(doc, 'text', 'summary')
        return sum_docs
    
    @staticmethod
    def email_context_for(event: dict, certainty: float = None) -> list[dict]:
        sum_email = BriefingSupport.context_for(event, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'email_id', certainty)  
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
