import time
import json
import os
import pytest
import requests
from library import weaviate as w
import library.handlers as h
from weaviate.classes.query import Filter
from requests.exceptions import ConnectionError

from library.utils import Utils
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase

class TestEmailWeaviate(IntegrationTestBase):
    
    def is_responsive(self, url):
        try:
            print("Checking if service is responsive at ", url, " ... ")
            response = requests.get(url)
            if response.status_code == 200:
                print("Service is responsive")
                return True
        except ConnectionError:
            return False

    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services):
        # """Ensure that service is up and responsive."""

        port = docker_services.port_for("weaviate", 8081)
        url = "http://{}:{}".format(docker_ip, port)
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.1, check=lambda: self.is_responsive(url)
        )
        return {
            'url': url,
            'host': docker_ip,
            'port': str(port)
        }

    def test_email_model_create(self, service):
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None

        response = weave.client.collections.list_all(simple=False)
        self.show_nested_properties_match(response, WeaviateSchemas.EMAIL)
        self.show_nested_properties_match(response, WeaviateSchemas.EMAIL_TEXT)

    def test_email_save(self, service):
        print("Testing Weaviate at ", service)
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        
        emails, texts = self.prepare_email_collections(weave)

        handler = h.Handlers(weave)
        handler.handle_email({
            "email_id": "abcdef",
            "history_id": "ghijkl",
            "thread_id": "mnopqr",
            "labels": ["label1", "label2"],
            "to": [
                {
                    "email": "him@that.com",
                    "name": "Him"
                }
            ],
            "cc": [
                {
                    "email": "yo@you.yu"
                }
            ],
            "bcc": [
                {
                    "email": "me@now.then",
                    "name": "Me"
             }
            ],
            "subject": "This is a test email",
            "from": {
                "email": "someone@important.special",
                "name": "Someone Important"
            },
            "date": "2021-01-01T12:34:56-06:00",
            "body": Utils.string_multiply("All work and no play makes for silly movies. ", 1000)

        })

        metadata = [e for e in emails.iterator()]
        text = [t for t in texts.iterator()]

        assert len(metadata) == 1, "There should only be one email"
        assert len(text) > 1, "There should only be one email text chunked into multiple segments"

        assert metadata[0].properties['email_id'] == "abcdef"
        assert metadata[0].properties['history_id'] == "ghijkl"
        assert metadata[0].properties['thread_id'] == "mnopqr"
        assert metadata[0].properties['subject'] == "This is a test email"
        assert metadata[0].properties['labels'] == ["label1", "label2"]
        assert metadata[0].properties['to'] == [
                {
                    "email": "him@that.com",
                    "name": "Him"
                }
            ]
        assert len(metadata[0].properties) == 10, "There should be 10 properties in an email"

        for chunk in text:
            assert 'text' in chunk.properties.keys()
            assert chunk.properties.get('email_id') == "abcdef"
            assert chunk.properties.get('thread_id') == "mnopqr"


    def prepare_email_collections(self, weave):
        emails = self.truncate_collection_and_return(weave, WeaviateSchemas.EMAIL)
        texts = self.truncate_collection_and_return(weave, WeaviateSchemas.EMAIL_TEXT)

        return emails, texts
    