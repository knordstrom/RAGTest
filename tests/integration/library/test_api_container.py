import pytest
import requests
from tests.integration.library.integration_test_base import IntegrationTestBase
import time

class TestApiContainer(IntegrationTestBase):
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

        service = {
            'weaviate': {
                'url': weaviate_url,
                'host': docker_ip,
                'port': str(weaviate_port)
            },
            'neo4j': {
                'url': neo4j_url,
                'host': docker_ip,
                'port': str(neo4j_port)
            },
            'api': {
                'url': api_url,
                'host': docker_ip,
                'port': str(api_port)
            }
        }
        return service

    '''
    briefs endpoint testing
    '''
    def test_briefs_endpoint_without_any_params(self, service):
        response = requests.get(f"http://localhost:{service['api']['port']}/briefs")
        print("response status code: ", response.status_code)
        assert response.status_code == 422

    def test_briefs_endpoint_without_email_params(self, service):
        params = {
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/briefs", params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 422

    def test_briefs_endpoint_without_start_params(self, service):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "end": "2024-07-30T17:00:00Z",
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/briefs", params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 422
    
    def test_briefs_endpoint_without_incorrect_threshold_params(self, service):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
            "threshold": "120"
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/briefs", params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 400
    
    def test_briefs_endpoint_without_incorrect_certainty_params(self, service):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
            "threshold": "120"
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/briefs", params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 400
    
    def test_briefs_endpoint_with_params(self, service):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/briefs", params=params)
        print("response status code: ", response.status_code)
        assert response.status_code == 200
    
    '''
    test schedule endpoint
    '''
    def test_schedule_endpoint_with_params(self, service):
        params = {
            "email": "emmasmithcto6306@gmail.com",
            "start": "2024-07-29T17:00:00Z",
            "end": "2024-07-30T17:00:00Z",
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/schedule", params=params)
        assert response.status_code == 200
    
    def test_schedule_endpoint_without_params(self, service):
        response = requests.get(url=f"http://localhost:{service['api']['port']}/schedule")
        assert response.status_code == 422
    
    '''
    test ask endpoint
    '''
    def test_ask_endpoint_with_params(self, service):
        params = {
            "query": "What is happening?",
            "n": 3
        }
        response = requests.get(url=f"http://localhost:{service['api']['port']}/ask", params=params)
        assert response.status_code == 200
    
    def test_ask_endpoint_without_params(self, service):
        
        response = requests.get(url=f"http://localhost:{service['api']['port']}/ask")
        assert response.status_code == 422
    