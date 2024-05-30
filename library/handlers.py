from library.slack import Slack
from library.utils import Utils
import library.weaviate as weaviate
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
import library.document_parser as DocumentParser
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
        if email['body'] == None or email['body'] == '':
            email['body'] = email['subject']
        self.w.upsertChunkedText(email, WeaviateSchemas.EMAIL_TEXT, WeaviateSchemas.EMAIL, 'body')

    def handle_event(self, event: dict):
        if event.get('description') == None or event.get('description') == '':
            event['description'] = event.get('summary', '')
        self.w.upsertChunkedText(event, WeaviateSchemas.EVENT_TEXT, WeaviateSchemas.EVENT, 'description')

    def handle_document(self, document: dict, filename: str = None):
        if filename == None:
            filename = self.get_file(document)
        text = DocumentParser.retrieve(filename)
        summary = self.summarizer.summarize(text)
        document['text'] = text
        self.w.upsertChunkedText(document, WeaviateSchemas.DOCUMENT_TEXT, WeaviateSchemas.DOCUMENT, 'text')
        self.w.upsert({'text': summary}, WeaviateSchemas.DOCUMENT_SUMMARY)

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
            'text': message['text'],
        }

        Utils.isoify(message_vdb, 'ts')
        return message_vdb, message_text_vdb


    def handle_slack_channel(self, slack: dict):
        print("Handling slack channel", slack.get('name', '???'), slack.keys())

        # upsert channel itself on channel id
        channel_vdb = self.format_channel(slack)
        print("Channel properties:", channel_vdb)

        self.w.upsert(channel_vdb, WeaviateSchemas.SLACK_CHANNEL)

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

                self.w.upsert(thread_vdb, WeaviateSchemas.SLACK_THREAD)
                for message_vdb, message_text_vdb in zip(messages_vdb, messages_text_vdb):
                    #TODO: upsert message_vdb
                    self.w.upsert(message_vdb, WeaviateSchemas.SLACK_MESSAGE)
                    self.w.upsert_text_vectorized(message_text_vdb['text'], message_text_vdb, WeaviateSchemas.SLACK_MESSAGE_TEXT)


class Summarizer:

    def __init__(self, client: Groq) -> None:
        self.client = client

    def summarize(self, text: str) -> str:
        prompt = """
You are a chief of staff for a vice president of engineering. Please briefly summarize the following document, including its purpose, 
key points, and any action items in no more than 5 sentences:
{document}
"""

        context = {
            'document': text
        }

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt.format(**context),
                }
            ],
            model="llama3-8b-8192",
            temperature=0.01,
            max_tokens=2000,
        )
        return chat_completion.choices[0].message.content