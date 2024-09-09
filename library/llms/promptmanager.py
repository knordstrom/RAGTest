import datetime
import json
import os
from cachetools import TTLCache, cached
import dotenv
import requests
from globals import Globals
from library.decorators import Decorators as d

class PromptManager:

    api_key: str = None
    base_url: str = "https://reineed-be-3qiddja7xa-ts.a.run.app/api/v1/"
    branch_id: str = "6669c0d6e881c714f04e4a49"

    headers: dict[str, str] = {
        "accept": "application/json",
        "api-key": "htfzvt8Mv0PyoIuJemScykmljemyHA2mNMYZ13XmprYxqF2KbC"
    }

    prompt_cache = {}
    cache_complete: datetime.datetime = None
    cache_timeout_seconds: int = 300 # 5 minutes

    def __new__(cls) -> None:
        if not hasattr(cls, 'instance'):
            cls.instance = super(PromptManager, cls).__new__(cls)
            self = cls.instance
            dotenv.load_dotenv()
            self.api_key = os.getenv("PROMPTTEAMS_API_KEY")
            self.cache_prompt_keys()
        return cls.instance    
    
    def cache_expired(self) -> bool:
        return (datetime.datetime.now() - self.cache_complete).seconds > self.cache_timeout_seconds
    
    def name_to_id(self, name: str) -> str:
        prompt_id: str = self.prompt_cache.get(name)
        if prompt_id is None or self.cache_expired():
            self.cache_prompt_keys()
            self.prompt_cache.get(name)
            prompt_id: str = self.prompt_cache.get(name)
        return prompt_id

    def get_latest_prompt_template(self, name: str) -> str:
        pd: dict[str, any] = self.get_prompt(name)
        prompt: list[dict[str, any]] = pd.get('versions',[])
        if len(prompt) == 0:
            raise PromptMissingException(f"No prompt versions found for name `{name}`")
        
        template = prompt[0].get('template')
        if (template is None):
            raise PromptMissingException(f"No template found for prompt `{name}`: {prompt}")
        return template

    def get_prompt(self, name: str) -> dict[str, str]:
        prompt_id: str = self.name_to_id(name)
        result: dict[str, str] = self.get_response("get-prompt", prompt_id)
        if not result or not result.get('versions'):
            try:
                with open(Globals().prompt(name), 'r') as f:
                    text = f.read()
                    result['versions'] = [{"template": text}]
            except FileNotFoundError:
                raise PromptMissingException(f"No prompt found for name `{name}`")
        return result

    def cache_prompt_keys(self) -> None:
        prompts: dict[str, any] = self.get_prompts()
        self.prompt_cache = {prompt["name"]: prompt["id"] for prompt in prompts}
        self.cache_complete: datetime.datetime = datetime.datetime.now()
        print("Prompt cache completed: ", self.prompt_cache)

    def get_prompts(self) -> dict[str, any]:
        result = self.get_response("get-prompts")
        return result

    @d.deep_freeze_args
    @cached(cache=TTLCache(maxsize=1024, ttl=86400))
    def get_response(self, request: str, prompt_name: str = None, params: dict[str, any] = {}) -> dict[str, any]:
        url: str = self.base_url + request
        req_params = {"branch_id": self.branch_id, "api-key": self.api_key}
        req_params.update(params)
        if prompt_name is not None:
            req_params.update({"prompt_name": prompt_name})
        response: requests.Response = requests.get(url, headers=self.headers, params=req_params)
        text = response.text
        if prompt_name is not None and (text is None or text == ""):
            text = Globals().prompt(request)
        return json.loads(text)
    
class PromptMissingException(Exception):
    pass