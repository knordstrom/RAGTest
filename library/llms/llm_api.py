from pydantic import Extra
import library.llms.llm as llm
import json
import requests
from typing import Any, List, Mapping, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM as LangChainBaseLLM

class LangLLM(LangChainBaseLLM):

    llm_url: str = None

    def __init__(self, host, port):
        super().__init__()
        self.llm_url = f'http://{host}:{port}/v1/completions'      

    @property
    def _llm_type(self) -> str:
        return "mistral-7b-instruct-v0.1.Q4_0"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        r = requests.post(self.llm_url, json.dumps({    
                'model': self._llm_type,
                'prompt': [prompt],
                'max_tokens': kwargs.get('max_tokens', 500),
                'temperature': 0,
                'end_id': 2,
                'pad_token': 2,
                'bad_words': '',
                'stop_words': ''
        }))
        r.raise_for_status()

        return r.json()['choices'][0]['text']

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"llmUrl": self.llm_url}
    

class ApiModel:
    
    def __init__(self, host, port):
        self.llm = LangLLM(host, port)

    def generate(self, prompt, max_tokens=500, temperature=0.0):
        response = self.llm._call(prompt, max_tokens=max_tokens, temperature = temperature)
        return response


class LLM_API(llm.LLM):
    def __init__(self, host, port, vdb):
        self.host = host
        self.port = port
        self.vdb = vdb
        self.model = ApiModel(host, port)
    




