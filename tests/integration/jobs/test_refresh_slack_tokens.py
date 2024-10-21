from datetime import datetime, timedelta
import os
import subprocess
from typing import Sequence
import dotenv
import pytest
import requests
from jobs.dags.refresh_slack_tokens import find_expiring_creds
from globals import Globals
from library.data.local.neo4j import Neo4j
from library.enums.data_sources import DataSources
from library.managers.auth_manager import AuthManager
from library.models.api_models import OAuthCreds, TokenResponse
from library.models.employee import User
from tests.integration.library.integration_test_base import IntegrationTestBase, MultiReadyResponse, ReadyResponse
import time
from dagster import AssetMaterialization, ExecuteInProcessResult, IntMetadataValue, JsonMetadataValue, MaterializeResult, materialize

class TestRefreshSlackTokens(IntegrationTestBase):
    docker_service_object: ReadyResponse

    def is_responsive(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except ConnectionError:
            return False


    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services) -> ReadyResponse:
        # """Ensure that service is up and responsive."""
        neo4j_port = docker_services.port_for("neo4j", 7575)
        neo4j_url = "http://{}:{}".format(docker_ip, neo4j_port)
        print("Checking if service is responsive at ", neo4j_url, " ... ")
        subprocess.run(["docker", "ps", "-a"])

        not_ready: bool = True
        tries: int = 5
        service: ReadyResponse = None
        while not_ready and tries > 0:
            try:
                docker_services.wait_until_responsive(
                    timeout=180.0, pause=0.1, check=lambda: self.is_responsive(neo4j_url)
                )
                service = ReadyResponse(
                        url=neo4j_url,
                        host=docker_ip,
                        port=str(neo4j_port)
                    )
                self.docker_service_object = service
                not_ready = False

            except Exception as e:
                print("Error: ", e)
                tries -= 1
                time.sleep(10)
        return service

    def test_refresh_slack_tokens_find_expiring_creds(self, service: ReadyResponse):
        neo = Neo4j()
        mg = AuthManager(neo)
        token: TokenResponse = neo.create_new_user("someone@somewhere.idk", "password")
        user: User = mg.datastore.get_user_by_email("someone@somewhere.idk")
        token_2: TokenResponse = neo.create_new_user("someone_else@somewhere.idk", "password")
        user_2: User = mg.datastore.get_user_by_email("someone_else@somewhere.idk")
        slack_creds_almost_expired: OAuthCreds = OAuthCreds(
            email=token.email,
            remote_target=DataSources.SLACK,
            token="slack_creds_almost_expired",
            refresh_token="refresh_slack_creds_almost_expired",
            expiry=datetime.now() - timedelta(minutes=11),
            client_id="id",
            client_secret="secret",
            token_uri="uri",
            scopes=["scope"]
        )

        slack_creds_current: OAuthCreds = OAuthCreds(
            email=token_2.email,
            remote_target=DataSources.SLACK,
            token="slack_creds_current",
            refresh_token="refresh_slack_creds_current",
            expiry=datetime.now() + timedelta(days=30),
            client_id="id",
            client_secret="secret",
            token_uri="uri",
            scopes=["scope"]
        )


        google_creds_expired: OAuthCreds = OAuthCreds(
            email=token.email,
            remote_target=DataSources.GOOGLE,
            token="google_creds_expired",
            refresh_token="refresh_google_creds_expired",
            expiry=datetime.now() + timedelta(minutes=11),
            client_id="id",
            client_secret="secret",
            token_uri="uri",
            scopes=["scope"]
        )
            
        neo.write_remote_credentials(user=user, creds=slack_creds_almost_expired)
        neo.write_remote_credentials(user=user_2, creds=slack_creds_current)
        neo.write_remote_credentials(user=user, creds=google_creds_expired)

        assert len(neo.read_all_creds()) == 3
        for c in neo.read_all_creds():
            print("CRED", c)

        result: ExecuteInProcessResult = materialize([find_expiring_creds])
        assert result is not None
        # time.sleep(500)

        result: Sequence[AssetMaterialization] = result.asset_materializations_for_node("find_expiring_creds")

        assert result is not None
        assert len(result) == 1

        result: AssetMaterialization = result[0]
        num_records: IntMetadataValue = result.metadata["num_records"]
        credentials: JsonMetadataValue = result.metadata["credentials"]
        
        assert result is not None
        assert num_records.value == 1
        assert credentials is not None
        assert len(credentials.value) == 1
        assert credentials.value[0]["email"] == slack_creds_almost_expired.email
        assert credentials.value[0]["remote_target"] == slack_creds_almost_expired.remote_target.value
        assert credentials.value[0]["token"] == slack_creds_almost_expired.token
        assert credentials.value[0]["refresh_token"] == slack_creds_almost_expired.refresh_token
        assert credentials.value[0]["expiry"] == slack_creds_almost_expired.expiry.isoformat()