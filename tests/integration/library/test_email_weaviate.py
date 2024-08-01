import pytest
import requests
from library import weaviate as w
import library.handlers as h
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

        response: dict[str, object] = weave.client.collections.list_all(simple=False)
        assert len(response.keys()) == len(WeaviateSchema.class_objs), "There should be collections in the Weaviate instance for each schema object"

        print("Collections: ", response)

        assert response.get("Email") is not None
        assert response.get("EmailText") is not None
        assert response.get("EmailThread") is not None

        self.show_nested_properties_match(response, WeaviateSchemas.EMAIL_THREAD)
        self.show_nested_properties_match(response, WeaviateSchemas.EMAIL)
        self.show_nested_properties_match(response, WeaviateSchemas.EMAIL_TEXT)

    def test_email_save(self, service):
        print("Testing Weaviate at ", service)
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        
        emails, texts = self.prepare_email_collections(weave)

        response = weave.client.collections.list_all(simple=False)
        print("Collections: ")
        [print(p) for p in response['Email'].properties]

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
                    "email": "him@that.com",
                    "name": "Him"
                }
            ],
            "bcc": [
                {
                    "email": "him@that.com",
                    "name": "Him"
                }
            ],
            "subject": "This is a test email",
            "from": {
                "email": "someone@important.special",
                "name": "Someone Important"
            },
            "provider": "Google",
            "date": "2021-01-01T12:34:56-06:00",
            "body": Utils.string_multiply("All work and no play makes for silly movies. ", 1000)

        })

        metadata = [e for e in emails.iterator()]
        text = [t for t in texts.iterator()]

        assert len(text) > 1, "The email text should be chunked into multiple segments"
        assert len(metadata) == 1, "There should be a single email metadata model saved"
        
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
        assert len(metadata[0].properties) ==11, "There should be 11 properties in an email, found " + str(len(metadata[0].properties))

        pertinent: list[dict[str, object]] = []
        for chunk in text:
            if chunk.properties.get('email_id') == "abcdef":
                pertinent.append(chunk)
            assert 'text' in chunk.properties.keys()
        
        assert len(pertinent) > 1, "There should be multiple text chunks saved for the email"
        for chunk in pertinent:
            assert chunk.properties.get('email_id') == "abcdef"
            assert chunk.properties.get('thread_id') == "mnopqr"
            assert chunk.properties.get('ordinal') is not None
            assert chunk.properties.get('date').isoformat() == "2021-01-01T12:34:56-06:00"

    def test_writing_email_text_is_idempotent(self, service):
        weave = w.Weaviate(port=service['port'], host=service['host'])
        assert weave is not None
        _, texts = self.prepare_email_collections(weave)

        text_to_insert = """On Fri, Jun 7, 2024 at 10:17AM David Starck via groups.io \u003Cdstarck=\nInfuse.us@groups.io\u003E wrote:\n-=-=-=-=-=-=-=-=-=-=-=-\nGroups.io Links: You receive all messages sent to this group.\nView/Reply Online (#8620): https://ctolunches.groups.io/g/worldwide/message/8620\nMute This Topic: https://groups.io/mt/106524657/6925688\nGroup Owner: worldwide+owner@ctolunches.groups.io\nUnsubscribe: https://ctolunches.groups.io/g/worldwide/unsub [keith@madsync.com]\n-=-=-=-=-=-=-=-=-=-=-=-
                                     
     I believe at this point if I had to only develop for iOS I'd still pick\nReact Native. Partially because I'm very familiar with the toolset, and I\ndon't particularly like iOS development. Swift is moving in the right\ndirection, but the pragmatist in me would choose RN, because if I did\ndecide to pull in Android it's not that much additional work to make sure\nit's shipping on both platforms. It's also, as David mentioned, cheaper to\nresource.\n\nI'm not sure I'd ever build an app for Android only at this point. iOS\nholds a good portion of the US market share, and in the apps I've built it\nends up being closer to 70% or more. I'd need a very strong reason to even\nconsider it.\n\nI will call out my least favorite thing about RN, which is managing\ndependencies. It's fine if you keep it up to date frequently, but bit rot\nis real... I've had a nightmare of a time with a handful of older apps that\nwent multiple years without maintenance."""

        for i in range(3):
            weave.upsert_text_vectorized(text_to_insert, {'email_id': 'ok', 'thread_id':'still ok'}, WeaviateSchemas.EMAIL_TEXT)  
            vals = [t for t in texts.iterator() if t.properties.get('email_id') == 'ok']
            assert len(vals) == 2, f"There should be 2 text chunks saved on iteration {i}"
        

    def prepare_email_collections(self, weave):
        emails = self.truncate_collection_and_return(weave, WeaviateSchemas.EMAIL)
        texts = self.truncate_collection_and_return(weave, WeaviateSchemas.EMAIL_TEXT)

        return emails, texts
    