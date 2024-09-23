from datetime import datetime, tzinfo
import dateutil
import dateutil.tz
import pytest
import requests
from library.data.external.gsuite import GSuite
from library.data.local import weaviate as w
from library.enums.data_sources import DataSources
from library.managers.auth_manager import AuthManager
import library.managers.handlers as h
from requests.exceptions import ConnectionError

from library.models.api_models import OAuthCreds
from library.models.employee import User
from library.utils import Utils
from library.models.weaviate_schemas import WeaviateSchema, WeaviateSchemas
from tests.integration.library.integration_test_base import IntegrationTestBase, MultiReadyResponse, ReadyResponse
from weaviate.collections.collection import Collection
from weaviate.collections.classes.internal import Object
from weaviate.collections.classes.types import Properties, References
from google.oauth2.credentials import Credentials

class TestGsuite(IntegrationTestBase):
    
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
    def service(self, docker_ip, docker_services) -> MultiReadyResponse:
        # """Ensure that service is up and responsive."""

        weaviate_config = self.get_config(docker_ip, docker_services, "weaviate", 8081)
        neo4j_config = self.get_config(docker_ip, docker_services, "neo4j", 7575)
        return MultiReadyResponse(weaviate = weaviate_config, neo4j = neo4j_config)
    
    def get_config(self, docker_ip, docker_services, service_name: str,default_port: int) -> ReadyResponse:
        port = docker_services.port_for(service_name, default_port)
        url = "http://{}:{}".format(docker_ip, port)
        print("port for service ", service_name, " is ", port)
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.1, check=lambda: self.is_responsive(url)
        )
        return ReadyResponse(url = url,host = docker_ip,port = str(port))

    def test_credential_read_and_write(self, service: MultiReadyResponse):
        user = User(id = "id1", email = "someone@cognimate.ai")
        gss = GSuite(user, "creds_filename")

        gss.is_local = False
        assert gss.is_local == False
        returned: Credentials = gss.get_existing_credentials()
        # assert returned is None

        AuthManager().write_remote_credentials(user, 
                                               target = "GOOGLE", 
                                               token = "notarealtoken", 
                                               refresh_token = "alsonotarealtoken", 
                                               expiry=datetime(2021, 1, 1, 1, 1, 1, 1, tzinfo=dateutil.tz.tzoffset(None, -7*3600)), 
                                               client_id = "nope", 
                                               client_secret = "uhuh", 
                                               scopes=["email", "profile"])
        proof:OAuthCreds = AuthManager().read_remote_credentials(user, DataSources.GOOGLE)
        assert proof is not None, "Proof is None"
        
        returned: Credentials = gss.get_existing_credentials()

        print("Returned ", returned)

        assert returned is not None
        assert returned.token == "notarealtoken"
        assert returned.refresh_token == "alsonotarealtoken"
        assert returned.client_id == "nope"
        assert returned.client_secret == "uhuh"
        assert returned.expiry == datetime(2021, 1, 1, 8, 1, 1, 1)
        assert returned.scopes == ["email", "profile"]

        assert returned.expired == True
        