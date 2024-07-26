import os
from library.groq_client import GroqClient
from library.promptmanager import PromptManager


class BriefingSummarizer:

    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        pass

    def summarize_with_prompt(self, prompt: str, context: dict[str, str]) -> str:
        pass

class GroqBriefingSummarizer(BriefingSummarizer):

    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        prompt = PromptManager().get_latest_prompt_template(prompt_name)  
        return self.summarize_with_prompt(prompt, context)
    
    def summarize_with_prompt(self, prompt: str, context: dict[str, str]) -> str:
        outcome = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=2000).query(prompt, context)
        return outcome