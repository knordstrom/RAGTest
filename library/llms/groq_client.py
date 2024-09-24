from enum import Enum
import os
from cachetools import TTLCache, cached
import dotenv
from groq import Groq

from library.decorators import Decorators as d

class Models(Enum):
    #     Supported Models
    # GroqCloud currently supports the following models:

    # Distil-Whisper English
    # Model ID: distil-whisper-large-v3-en
    # Developer: HuggingFace
    # Max File Size: 25 MB
    DISTIL_WHISPER_LARGE_V3_EN = "distil-whisper-large-v3-en"

    # Gemma 2 9B
    # Model ID: gemma2-9b-it
    # Developer: Google
    # Context Window: 8,192 tokens
    GEMMA2_9B_IT = "gemma2-9b-it"

    # Gemma 7B
    # Model ID: gemma-7b-it
    # Developer: Google
    # Context Window: 8,192 tokens
    GEMMA_7B_IT = "gemma-7b-it"

    # Llama 3 Groq 70B Tool Use (Preview)
    # Model ID: llama3-groq-70b-8192-tool-use-preview
    # Developer: Groq
    # Context Window: 8,192 tokens
    LLAMA3_GROQ_70B_8192 = "llama3-groq-70b-8192"

    # Llama 3 Groq 8B Tool Use (Preview)
    # Model ID: llama3-groq-8b-8192-tool-use-preview
    # Developer: Groq
    # Context Window: 8,192 tokens
    LLAMA3_GROQ_8B_8192_TOOL_USE = "llama3-groq-8b-8192-tool-use-preview"

    # Llama 3.1 405B
    # Offline due to overwhelming demand! Stay tuned for updates.
    # Llama 3.1 70B (Preview)
    # Model ID: llama-3.1-70b-versatile
    # Developer: Meta
    # Context Window: 131,072 tokens    
    LLAMA_31_70B_VERSATILE = "llama-3.1-70b-versatile"

    # Llama 3.1 8B (Preview)
    # Model ID: llama-3.1-8b-instant
    # Developer: Meta
    # Context Window: 131,072 tokens
    LLAMA_31_8B_INSTANT = "llama-3.1-8b-instant"

    # Llama Guard 3 8B
    # Model ID: llama-guard-3-8b
    # Developer: Meta
    # Context Window: 8,192 tokens
    LLAMA_GUARD_3_8B = "llama-guard-3-8b"

    # LLaVA 1.5 7B
    # Model ID: llava-v1.5-7b-4096-preview
    # Developer: Haotian Liu
    # Context Window: 4,096 tokens
    LLAVA_V15_7B_4096 = "llava-v1.5-7b-4096-preview"

    # Meta Llama 3 70B
    # Model ID: llama3-70b-8192
    # Developer: Meta
    # Context Window: 8,192 tokens
    LLAMA3_70B_8192 = "llama3-70b-8192"

    # Meta Llama 3 8B
    # Model ID: llama3-8b-8192
    # Developer: Meta
    # Context Window: 8,192 tokens
    LLAMA3_8B_8192 = "llama3-8b-8192"

    # Mixtral 8x7B
    # Model ID: mixtral-8x7b-32768
    # Developer: Mistral
    # Context Window: 32,768 tokens
    MIXTRAL_8X7B_32768 = "mixtral-8x7b-32768"

    # Whisper
    # Model ID: whisper-large-v3
    # Developer: OpenAI
    # File Size: 25 MB
    WHISPER_LARGE_V3 = "whisper-large-v3"

    @staticmethod
    def default() -> 'Models':
        dotenv.load_dotenv()
        default: str = os.getenv("GROQ_DEFAULT_MODEL")
        default = default.strip().upper().replace("-", "_") if default else None
        if default is not None and default in Models.__members__:
            return Models.__members__[default]
        return Models.LLAMA3_70B_8192

class GroqClient:

    key: str
    model: Models
    temperature: float
    max_tokens: int

    def __init__(self, key: str, model: Models = None, temperature: float=0.01, max_tokens: int=2000):
        self.key = key
        self.model = model if model else Models.default()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Groq(
            api_key=key
        )

    @d.deep_freeze_args
    @cached(cache=TTLCache(maxsize=1024, ttl=3600))
    def query(self, prompt: str, context: dict[str, str]) -> str:
        prompt_len: int = len(prompt.format(**context))
        model = self.model.value if prompt_len < 8192 else Models.LLAMA_31_8B_INSTANT.value
        print("Querying GROQ with model: ", model, "and", len(prompt.format(**context)),"characters of input")

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt.format(**context),
                }
            ],
            model=model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return chat_completion.choices[0].message.content