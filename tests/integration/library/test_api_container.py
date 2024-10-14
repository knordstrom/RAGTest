import pytest
import requests
from library.managers.auth_manager import AuthManager
from library.models.api_models import TokenResponse
from tests.integration.library.integration_test_base import IntegrationTestBase, MultiReadyResponse, ReadyResponse
import time

class TestApiContainer(IntegrationTestBase):
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

        weaviate_port = docker_services.port_for("weaviate", 8081)
        weaviate_url = "http://{}:{}".format(docker_ip, weaviate_port)
        print("Checking if service is responsive at ", weaviate_url, " ... ")
        time.sleep(60)
        docker_services.wait_until_responsive(
            timeout=180.0, pause=0.1, check=lambda: self.is_responsive(weaviate_url)
        )
        neo4j_port = docker_services.port_for("neo4j", 7575)
        neo4j_url = "http://{}:{}".format(docker_ip, neo4j_port)
        print("Checking if service is responsive at ", neo4j_url, " ... ")
        docker_services.wait_until_responsive(
            timeout=180.0, pause=0.1, check=lambda: self.is_responsive(neo4j_url)
        )
        api_port = docker_services.port_for("api", 5010)
        api_url = "http://{}:{}/status".format(docker_ip, api_port)
        print("Checking if service is responsive at ", api_url, " ... ")
        docker_services.wait_until_responsive(
            timeout=120.0, pause=0.1, check=lambda: self.is_responsive(api_url)
        )

        token: TokenResponse = AuthManager().datastore.create_new_user(email="emmasmithcto6306@gmail.com", password="password")

        service = MultiReadyResponse(
            weaviate=ReadyResponse(
                url=weaviate_url,
                host=docker_ip,
                port=str(weaviate_port)
            ),
            neo4j = ReadyResponse(
                url=neo4j_url,
                host=docker_ip,
                port=str(neo4j_port)
            ),
            api = ReadyResponse(
                url = api_url,
                host = docker_ip,
                port = str(api_port)
            ),
            token = token
        )
        self.docker_service_object = service
        return service

    def _make_api_get_request(self, endpoint: str, service: MultiReadyResponse, params: dict[str, str] = {}, headers: dict[str, str] = {}):
        headers["Authorization"] = f"Bearer {service.token.access_token}"
        response = requests.get(url=f"http://localhost:{service.api.port}/{endpoint}", params=params, headers=headers)
        return response

    '''
    briefs endpoint testing
    '''
    def test_briefs_endpoint_without_any_params(self, service: MultiReadyResponse):
        response = self._make_api_get_request(endpoint="briefs", service=service)
        print("response status code: ", response.status_code)
        assert response.status_code == 422

    def test_briefs_endpoint_without_email_params(self, service: MultiReadyResponse):
        params = {
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = self._make_api_get_request(endpoint="briefs", service=service, params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 422

    def test_briefs_endpoint_without_start_params(self, service: MultiReadyResponse):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "end": "2024-07-30T17:00:00Z",
        }
        response = self._make_api_get_request(endpoint="briefs", service=service, params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 422
    
    def test_briefs_endpoint_without_incorrect_threshold_params(self, service: MultiReadyResponse):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
            "threshold": "120"
        }
        response = self._make_api_get_request(endpoint="briefs", service=service, params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 400
    
    def test_briefs_endpoint_without_incorrect_certainty_params(self, service: MultiReadyResponse):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
            "threshold": "120"
        }
        response = self._make_api_get_request(endpoint="briefs", service=service, params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 400
    
    def test_briefs_endpoint_with_params(self, service: MultiReadyResponse):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = self._make_api_get_request(endpoint="briefs", service=service, params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 200
    
    '''
    test schedule endpoint
    '''
    def test_schedule_endpoint_with_params(self, service: MultiReadyResponse):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = self._make_api_get_request(endpoint="schedule", service=service, params=params)
        assert response.status_code == 200
    
    def test_schedule_endpoint_without_params(self, service: MultiReadyResponse):
        response = self._make_api_get_request(endpoint="schedule", service=service)
        assert response.status_code == 422
    
    '''
    test ask endpoint
    '''
    def test_ask_endpoint_with_params(self, service: MultiReadyResponse):
        params = {
            "query": "What is happening?",
            "n": 3
        }
        response = self._make_api_get_request(endpoint="ask", service=service, params=params)
        print("Reponse was", response.raw)
        assert response.status_code == 200
    
    def test_ask_endpoint_without_params(self, service: MultiReadyResponse):
        response = self._make_api_get_request(endpoint="ask", service=service)
        assert response.status_code == 422
    