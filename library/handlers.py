import library.weaviate as weaviate
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
        self.w.upsertChunkedText(email, weaviate.WeaviateSchemas.EMAIL_TEXT, weaviate.WeaviateSchemas.EMAIL, 'body')

    def handle_event(self, event: dict):
        if event.get('description') == None or event.get('description') == '':
            event['description'] = event.get('summary', '')
        self.w.upsertChunkedText(event, weaviate.WeaviateSchemas.EVENT_TEXT, weaviate.WeaviateSchemas.EVENT, 'description')

    def handle_document(self, document: dict, filename: str = None):
        if filename == None:
            filename = self.get_file(document)
        text = DocumentParser.retrieve(filename)
        summary = self.summarizer.summarize(text)
        document['text'] = text
        self.w.upsertChunkedText(document, weaviate.WeaviateSchemas.DOCUMENT_TEXT, weaviate.WeaviateSchemas.DOCUMENT, 'text')
        self.w.upsert({'text': summary}, weaviate.WeaviateSchemas.DOCUMENT_SUMMARY)

    def get_file(document: dict):
        url = document['url']
        response = requests.get(url)
        contents = response.text
        # Save contents to a temporary unique filename
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(contents.encode())
            temp_filename = temp_file.name

        return temp_filename


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