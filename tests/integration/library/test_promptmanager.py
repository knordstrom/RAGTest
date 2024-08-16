import pytest
from library.promptmanager import PromptMissingException, PromptManager
from tests.integration.library.integration_test_base import IntegrationTestBase


class TestPromptManager(IntegrationTestBase):

    @pytest.fixture(scope="session")
    def service(self, docker_ip, docker_services):
        return {}

    def test_prompt_teams_caches_prompts(self, service):     
        pt = PromptManager()
        assert pt is not None
        assert pt.prompt_cache is not None
        assert 'BriefingSupport.create_briefings_for' in pt.prompt_cache.keys()
    
    def test_prompt_teams_gets_prompt(self, service): 
        pt = PromptManager()
        assert pt is not None
        prompt = pt.get_prompt('BriefingSupport.create_briefings_for')
        print(prompt)
        assert prompt is not None
        assert prompt['name'] == 'BriefingSupport.create_briefings_for'
        assert prompt.get('versions') is not None
        assert len(prompt['versions']) > 0

        try:
            prompt = pt.get_prompt('this is not a prompt')
            assert False, "A prompt for an incorrect name should have raised an exception"
        except PromptMissingException as e:
            assert True
        except Exception as e:
            assert False, "An exception that doesn't match the type was raised for a missing prompt"