from datetime import datetime, timedelta
import os
import subprocess
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

class TestRefreshSlackTokens(IntegrationTestBase):
    docker_service_object: MultiReadyResponse

    def is_responsive(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except ConnectionError:
            return False


    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services):
        # """Ensure that service is up and responsive."""
        neo4j_port = docker_services.port_for("neo4j", 7575)
        neo4j_url = "http://{}:{}".format(docker_ip, neo4j_port)
        print("Checking if service is responsive at ", neo4j_url, " ... ")
        time.sleep(10)
        subprocess.run(["docker", "ps", "-a"])
        docker_services.wait_until_responsive(
            timeout=180.0, pause=0.1, check=lambda: self.is_responsive(neo4j_url)
        )
        service = MultiReadyResponse(
            neo4j = ReadyResponse(
                url=neo4j_url,
                host=docker_ip,
                port=str(neo4j_port)
            ),
        )
        self.docker_service_object = service
        return service

    def test_refresh_slack_tokens_find_expiring_creds(self, service):
        neo = Neo4j()
        mg = AuthManager(neo)
        user: User = neo.create_new_user("someone@somewhere.idk", "password")
        slack_creds_almost_expired: OAuthCreds = OAuthCreds(
            email=user.email,
            remote_target=DataSources.SLACK,
            token="slack_creds_almost_expired",
            refresh_token="refresh_slack_creds_almost_expired",
            expiry=datetime.now() - timedelta(hours=11),
            client_id="id",
            client_secret="secret",
            token_uri="uri",
            scopes=["scope"]
        )

        slack_creds_current: OAuthCreds = OAuthCreds(
            email=user.email,
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
            email=user.email,
            remote_target=DataSources.GOOGLE,
            token="google_creds_expired",
            refresh_token="refresh_google_creds_expired",
            expiry=datetime.now() + timedelta(days=1),
            client_id="id",
            client_secret="secret",
            token_uri="uri",
            scopes=["scope"]
        )
            
        neo.write_remote_credentials(user=user, creds=slack_creds_almost_expired)
        neo.write_remote_credentials(user=user, creds=slack_creds_current)
        neo.write_remote_credentials(user=user, creds=google_creds_expired)

        result = find_expiring_creds.execute_in_process()
        assert result is not None