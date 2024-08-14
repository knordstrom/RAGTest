import pytest
import requests
from library import weaviate as w
import library.handlers as h
from requests.exceptions import ConnectionError

from library.utils import Utils
from library.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase
from weaviate.collections.collection import Collection
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import Properties, References

class TestTransccriptsWeaviate(IntegrationTestBase):
    
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

    def test_transcript_model_create(self, service):
        weave: w.Weaviate = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None

        response: dict[str, object] = weave.client.collections.list_all(simple=False)
        assert len(response.keys()) == len(WeaviateSchema.class_objs), "There should be collections in the Weaviate instance for each schema object"

        print("Collections: ", response)

        assert response.get("Transcript") is not None
        assert response.get("TranscriptEntry") is not None