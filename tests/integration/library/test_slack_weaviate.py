import json
import os
import pytest
import requests
from library import weaviate as w
import library.handlers as h
from weaviate.classes.query import Filter
from requests.exceptions import ConnectionError

from library.weaviate_schemas import WeaviateSchemas

class TestSlackWeaviate:
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
        """Ensure that service is up and responsive."""

        # `port_for` takes a container port and returns the corresponding host port
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
    
    def test_slack_channel_save(self, service):
        print("Testing Weaviate at ", service)
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        channels = weave.collection(WeaviateSchemas.SLACK_CHANNEL)
        channels.data.delete_many(
            where = Filter.by_property("name").like("*"),
        )

        file_path = os.path.join(os.path.dirname(__file__), '../../resources', 'slack_response.json')
        with open(file_path) as json_file:

            slack = json.load(json_file)

            print()
            handler = h.Handlers(weave)
            handler.handle_slack_channel(slack[0])

            assert channels is not None

            result = []
            for channel in channels.iterator():
                print("Found channel", channel.properties['name'])
                result.append(channel)
            
            assert len(result) == 1


        
 