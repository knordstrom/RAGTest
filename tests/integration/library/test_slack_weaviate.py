import json
import os
import pytest
import requests
from library import weaviate as w
import library.handlers as h
from requests.exceptions import ConnectionError

from library.weaviate_schemas import WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase

class TestSlackWeaviate(IntegrationTestBase):

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
    
    def test_slack_model_create(self, service):
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None

        response = weave.client.collections.list_all(simple=False)
        self.show_nested_properties_match(response, WeaviateSchemas.SLACK_CHANNEL)
        self.show_nested_properties_match(response, WeaviateSchemas.SLACK_MESSAGE)
        self.show_nested_properties_match(response, WeaviateSchemas.SLACK_THREAD)
        self.show_nested_properties_match(response, WeaviateSchemas.SLACK_MESSAGE_TEXT)
    

    def test_slack_channel_save(self, service):
        print("Testing Weaviate at ", service)
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        
        channels, threads, messages, texts = self.prepare_slack_collections(weave)

        file_path = os.path.join(os.path.dirname(__file__), '../../resources', 'slack_response.json')
        with open(file_path) as json_file:

            slack = json.load(json_file)
            handler = h.Handlers(weave)
            handler.handle_slack_channel(slack[0])

            SlackChannelAssertions.show_channel_properties_saved(channels)
            SlackChannelAssertions.show_thread_properties_saved(threads)
            SlackChannelAssertions.show_message_properties_saved(messages)
            SlackChannelAssertions.show_text_properties_saved(texts)

    def prepare_slack_collections(self, weave):
        channels = self.truncate_collection_and_return(weave, WeaviateSchemas.SLACK_CHANNEL)
        threads = self.truncate_collection_and_return(weave, WeaviateSchemas.SLACK_THREAD)
        messages = self.truncate_collection_and_return(weave, WeaviateSchemas.SLACK_MESSAGE)
        texts = self.truncate_collection_and_return(weave, WeaviateSchemas.SLACK_MESSAGE_TEXT)
        return channels, threads, messages, texts
 

class SlackChannelAssertions:

    def show_channel_properties_saved(channels):
        result = []
        for channel in channels.iterator():
            print("Found channel", channel.properties['name'])
            result.append(channel)

        assert len(result) == 1, "There should only be one channel"

        channel = result[0]
        
        assert 'updated' in channel.properties.keys()
        assert 'creator' in channel.properties.keys()
        assert channel.properties['name'] == "random"
        assert channel.properties['channel_id'] == "C06DKQJ48TZ"
        assert channel.properties['is_private'] == False
        assert channel.properties['is_shared'] == False
        assert channel.properties['num_members'] == 4

    def show_thread_properties_saved(threads):
        result = []
        for thread in threads.iterator():
            print("Found thread", thread.properties['thread_id'])
            result.append(thread)

        assert len(result) == 4, "There should be 4 threads in the channel"

        thread = result[0]

        assert len(thread.properties.keys()) == 3, "There should be 2 properties in each thread"
        assert 'thread_id' in thread.properties.keys()
        assert thread.properties['channel_id'] == "C06DKQJ48TZ"

    def show_message_properties_saved(messages):
        result = []
        for message in messages.iterator():
            print("Found message", message.properties['message_id'])
            result.append(message)

        assert len(result) == 16, "There should be 16 messages in the channel"

        message = result[0]

        assert len(message.properties.keys()) == 6, "Each message should have 6 properties"

        assert 'message_id' in message.properties.keys()
        assert 'from' in message.properties.keys()
        assert 'ts' in message.properties.keys()
        assert 'subtype' in message.properties.keys()
        assert 'type' in message.properties.keys()
        assert 'thread_id' in message.properties.keys()

    def show_text_properties_saved(texts):
        result = []
        for text in texts.iterator():
            print("Found text", text.properties['message_id'])
            result.append(text)

        assert len(result) >= 16, "There should be at least one text chunk per message in the channel"

        text = result[0]

        assert len(text.properties.keys()) == 4, "Each text chunk should have 4 properties"

        assert 'message_id' in text.properties.keys()
        assert 'text' in text.properties.keys()
        assert 'thread_id' in text.properties.keys()
        
    