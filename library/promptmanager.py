import datetime
import json
import os
import dotenv
import requests

class PromptManager:

    base_url = "https://reineed-be-3qiddja7xa-ts.a.run.app/api/v1/"
    branch_id = "6669c0d6e881c714f04e4a49"

    headers = {
        "accept": "application/json",
        "api-key": "htfzvt8Mv0PyoIuJemScykmljemyHA2mNMYZ13XmprYxqF2KbC"
    }

    prompt_cache = {}
    cache_complete = None
    cache_timeout_seconds = 300 # 5 minutes

    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(PromptManager, cls).__new__(cls)
            self = cls.instance
            dotenv.load_dotenv()
            self.api_key = os.getenv("PROMPTTEAMS_API_KEY")
            self.cache_prompt_keys()
        return cls.instance    
    
    def cache_expired(self):
        return (datetime.datetime.now() - self.cache_complete).seconds > self.cache_timeout_seconds
    
    def name_to_id(self, name: str):
        prompt_id = self.prompt_cache.get(name)
        if prompt_id is None or self.cache_expired():
            self.cache_prompt_keys()
            self.prompt_cache.get(name)
            prompt_id = self.prompt_cache.get(name)
        if prompt_id is None:
            raise PromptMissingException(f"Prompt not found for name `{name}`")
        return prompt_id

    def get_latest_prompt_template(self, name: str):
        pd = self.get_prompt(name)
        prompt = pd.get('versions',[])
        if len(prompt) == 0:
            raise PromptMissingException(f"No prompt versions found for name `{name}`")
        
        template = prompt[0].get('template')
        if (template is None):
            raise PromptMissingException(f"No template found for prompt `{name}`: {prompt}")
        return template

    def get_prompt(self, name: str):
        prompt_id = self.name_to_id(name)
        result = self.get_response("get-prompt", {"prompt_id": prompt_id})
        return result

    def cache_prompt_keys(self):
        prompts = self.get_prompts()
        self.prompt_cache = {prompt["name"]: prompt["id"] for prompt in prompts}
        self.cache_complete = datetime.datetime.now()
        print("Prompt cache completed: ", self.prompt_cache)

    def get_prompts(self):
        result = self.get_response("get-prompts", {})
        return result


    def get_response(self, request: str, params: dict) -> dict:
        url = self.base_url + request
        params.update({"branch_id": self.branch_id, "api-key": self.api_key})
        response = requests.get(url, headers=self.headers, params=params)
        return json.loads(response.text)
    
class PromptMissingException(Exception):
    pass