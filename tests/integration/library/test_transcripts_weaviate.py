import pytest
import requests
from library.data.local import weaviate as w
from library.models.api_models import TranscriptConversation, TranscriptLine
import library.managers.handlers as h
from requests.exceptions import ConnectionError

from library.utils import Utils
from library.models.weaviate_schemas import WeaviateSchema, WeaviateSchemas
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
            timeout=60.0, pause=0.1, check=lambda: self.is_responsive(url)
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

        self.show_nested_properties_match(response, WeaviateSchemas.TRANSCRIPT)
        self.show_nested_properties_match(response, WeaviateSchemas.TRANSCRIPT_ENTRY)

    def test_transcript_save(self, service):
        weave: w.Weaviate = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None

        transcripts, transcript_entries = self.prepare_collections(weave)

        assert len(transcripts) == 0
        assert len(transcript_entries) == 0

        handler = h.Handlers(weave)
        handler.handle_transcript(TranscriptConversation(
            transcript_id="1",
            meeting_code="1",
            provider="Zoom",
            title="Meeting",
            attendee_names=["Alice", "Bob"],
            conversation=[
                TranscriptLine(
                    speaker="Alice",
                    text="Hello",
                    ordinal=0
                ),
                TranscriptLine(
                    speaker="Bob",
                    text="Hi",
                    ordinal=1
                )
            ]
        ))

        conversations = weave.get_transcript_conversations()
        assert len(conversations) == 1
        assert conversations[0] == TranscriptConversation(
            transcript_id="1",
            meeting_code="1",
            provider="Zoom",
            title="Meeting",
            attendee_names=["Alice", "Bob"],
            conversation=[
                
            ]
        )

        entries = weave.get_transcript_conversation_entries_for_id("1")
        assert len(entries) == 2
        assert entries[0] == TranscriptLine(
            speaker="Alice",
            text="Hello",
            ordinal=0
        )
        assert entries[1] == TranscriptLine(
            speaker="Bob",
            text="Hi",
            ordinal=1
        )

        convo = weave.get_transcript_conversation_by_meeting_code("1")
        assert convo == TranscriptConversation(
            transcript_id="1",
            meeting_code="1",
            provider="Zoom",
            title="Meeting",
            attendee_names=["Alice", "Bob"],
            conversation=[
                TranscriptLine(
                    speaker="Alice",
                    text="Hello",
                    ordinal=0
                ),
                TranscriptLine(
                    speaker="Bob",
                    text="Hi",
                    ordinal=1
                )
            ]
        )


    def prepare_collections(self, weave) -> tuple[Collection[Properties, References], Collection[Properties, References]]:
        transcripts = self.truncate_collection_and_return(weave, WeaviateSchemas.TRANSCRIPT)
        transcript_entries = self.truncate_collection_and_return(weave, WeaviateSchemas.TRANSCRIPT_ENTRY)

        return transcripts, transcript_entries   