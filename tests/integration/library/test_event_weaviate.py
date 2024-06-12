import ast
import time
import json
import os
import pytest
import requests
from library import models, weaviate as w
import library.handlers as h
from weaviate.classes.query import Filter
from requests.exceptions import ConnectionError

from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase

class TestEventWeaviate(IntegrationTestBase):
    
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

    def test_event_model_create(self, service):
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None

        response = weave.client.collections.list_all(simple=False)
        self.show_nested_properties_match(response, WeaviateSchemas.EVENT)
        self.show_nested_properties_match(response, WeaviateSchemas.EVENT_TEXT)

    def test_event_save_from_email(self, service):
        print("Testing Weaviate at ", service)
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        
        events, texts = self.prepare_event_collections(weave)

        resource = os.path.dirname(__file__) + "/../../resources/sample_email.json"
        assert os.path.exists(resource), "Resource file at " + resource + " does not exist"

        with open(resource, "r") as email_json:
            #four messages in the file, first 3 have no events
            for _ in range(3):
               email_json.readline()

            email_obj = models.Message.extract_data(ast.literal_eval(email_json.readline()))
            
            assert(len(email_obj.get('events', []))) != 0, "The email object should have an event in it"

            print(email_obj.get('events', []))
            handler = h.Handlers(weave)
            
            handler.handle_event(email_obj['events'][0])
            saved_texts = [t for t in texts.iterator()]
            assert len(saved_texts) >= 1, "There should be an event text saved in the system"

            saved_events = [e for e in events.iterator()]
            assert len(saved_events) == 1, "There should be an event saved in the system"

            print("Event ", saved_events[0])
            print("Text ", saved_texts[0])


    def prepare_event_collections(self, weave):
        event = self.truncate_collection_and_return(weave, WeaviateSchemas.EVENT)
        text = self.truncate_collection_and_return(weave, WeaviateSchemas.EVENT_TEXT)
        return event, text
    