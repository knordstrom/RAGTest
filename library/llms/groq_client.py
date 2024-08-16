from cachetools import TTLCache, cached
from groq import Groq

from library.decorators import Decorators as d


class GroqClient:

    def __init__(self, key: str, model: str = "llama3-70b-8192", temperature: float=0.01, max_tokens: int=2000):
        self.key = key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Groq(
            api_key=key
        )

    @d.deep_freeze_args
    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    def query(self, prompt: str, context: dict[str, str]) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt.format(**context),
                }
            ],
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return chat_completion.choices[0].message.content