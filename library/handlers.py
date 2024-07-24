import groq
from library.models.event import Event
from library.promptmanager import PromptManager
from library.slack import Slack
from library.utils import Utils
import library.weaviate as weaviate
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from groq import Groq
from dotenv import load_dotenv
import os
import requests
import tempfile


class Handlers:

    def __init__(self, w: weaviate.Weaviate, g: Groq = None) -> None:
        self.w = w
        self.summarizer = Summarizer(g)

    def handle_email(self, email: dict):
        if email.get('body', '') == '':
            email['body'] = email['subject']
        self.w.upsert_chunked_text(email, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'body')

    def handle_event(self, event: Event):
        if event.description == '' or event.description is None:
            event.description = event.summary
        event_dict = event.model_dump(exclude_none = True)
        Utils.rename_key(event_dict, 'from_', 'from')
        self.w.upsert_chunked_text(event_dict, WeaviateSchemas.EVENT_TEXT, WeaviateSchemas.EVENT, 'description')

    def handle_document(self, document: dict, filename: str = None):
        text = document.get("text")
        summary = self.summarizer.summarize(text)
        self.w.upsert_chunked_text(document, WeaviateSchemas.DOCUMENT_TEXT, WeaviateSchemas.DOCUMENT, 'text')
        self.w.upsert({'text': summary, 
        'document_id': document.get('document_id')}, WeaviateSchemas.DOCUMENT_SUMMARY)

    def get_file(self, document: dict):
        url = document['url']
        response = requests.get(url)
        contents = response.text
        # Save contents to a temporary unique filename
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(contents.encode())
            temp_filename = temp_file.name

        return temp_filename
        
    def format_channel(self, slack: dict):
        properties = map( lambda p: p.name, WeaviateSchema.class_map[WeaviateSchemas.SLACK_CHANNEL]["properties"])
        channel = {key: slack.get(key) for key in properties}
        channel['channel_id'] = slack['id'] 
        channel['creator'] = Slack.user_ids_to_emails.get(slack['creator'], slack['creator'])
        Utils.isoify(channel, 'updated')
        return channel

    def format_thread(self, thread: dict, channel_id: str):
        return {
            'thread_id': thread['id'],
            'channel_id': channel_id,
        }

    def format_message(self, message, thread_id):

        message_vdb = {
            'message_id': f"{thread_id}|{message['ts']}",
            'thread_id': thread_id,
            'from': Slack.user_ids_to_emails.get(message['user'], message['user']),
            'ts': message['ts'],
            'type': message['type'],
            'subtype': message.get('subtype'),
        }

        message_text_vdb = {
            'message_id': message_vdb['message_id'],
            'thread_id': thread_id,
            'text': message['text'],
        }

        Utils.isoify(message_vdb, 'ts')
        return message_vdb, message_text_vdb


    def handle_slack_channel(self, slack: dict):
        print("Handling slack channel", slack.get('name', '???'), slack.keys())

        # upsert channel itself on channel id
        channel_vdb = self.format_channel(slack)
        print("Channel properties:", channel_vdb)

        self.w.upsert(channel_vdb, WeaviateSchemas.SLACK_CHANNEL, 'channel_id')

        threads = slack.get('threads', [])
        print("     Threads", len(threads))

        for thread in threads:
            thread_vdb = self.format_thread(thread, slack['id'])
            thread_id = thread['id']
            messages_vdb = []
            messages_text_vdb = []
            for message in thread['messages']:
                if message.get('subtype') == 'channel_join':
                    continue
                message_vdb, message_text_vdb = self.format_message(message, thread_id)
                messages_vdb.append(message_vdb)
                messages_text_vdb.append(message_text_vdb)
    
            if len(messages_vdb) > 0:
                print('         Thread: ', thread_vdb)
                print('                            Messages:', len(messages_vdb))
                print('                            Message: ', messages_vdb[0])
                print('                            Text: ', messages_text_vdb[0])

                self.w.upsert(thread_vdb, WeaviateSchemas.SLACK_THREAD, 'thread_id')
                for message_vdb, message_text_vdb in zip(messages_vdb, messages_text_vdb):
                    #TODO: upsert message_vdb
                    self.w.upsert(message_vdb, WeaviateSchemas.SLACK_MESSAGE, 'message_id')
                    self.w.upsert_text_vectorized(message_text_vdb['text'], message_text_vdb, WeaviateSchemas.SLACK_MESSAGE_TEXT)


class Summarizer:

    def __init__(self, client: Groq) -> None:
        self.client = client

    def summarize(self, text: str) -> str:
        prompt = PromptManager().get_latest_prompt_template("Summarizer.summarize")

        context = {
            'document': text
        }

        content = prompt.format(**context)

        # default has been to use "llama3-8b-8192", however this model only allows 8kb of content rather than 32kb
        # mixtral is rate limited so we use it sparingly
        # tokens cover ~4 bytes, so we check if the content is greater than 4*8192
        model = "mixtral-8x7b-32768" if len(content) > 4*8192 else "llama3-8b-8192"


        print("     * Summarizing '" + text[:100] + " of length " + str(len(text)) + " using model " + model + " ...")
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ],

                model=model, 
                temperature=0.01,
                max_tokens=2000,
            )
            print("          ... summary complete")
            print("                                 >>>>>", chat_completion.choices[0].message.content[:10000])
            return chat_completion.choices[0].message.content
        except groq.RateLimitError as e:
            print("Rate limit error: ", e)
            return "Rate limit error, content too long to summarize."

        