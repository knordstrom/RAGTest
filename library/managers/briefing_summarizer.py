import os
import re
from library.llms.groq_client import GroqClient, Models
from library.llms.promptmanager import PromptManager


class BriefingSummarizer:

    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        pass

    def summarize_with_prompt(self, prompt: str, context: dict[str, str]) -> str:
        pass

    def generate_hyde_content(self, search_string: str) -> str:
        pass

class GroqBriefingSummarizer(BriefingSummarizer):

    max_tokens: int
    def __init__(self, max_tokens: int = 2000) -> None:
        self.max_tokens = max_tokens

    prompt_manager: PromptManager = PromptManager()

    def summarize(self, prompt_name: str, context: dict[str, str]) -> str:
        prompt: str = self.prompt_manager.get_latest_prompt_template(prompt_name)  
        return self.summarize_with_prompt(prompt, context)
    
    def summarize_with_prompt(self, prompt: str, context: dict[str, str], model: Models = None) -> str:
        prompt = prompt + """

        Please output the requested results within an XML block <response></response>."""

        outcome = GroqClient(os.getenv('GROQ_API_KEY'), max_tokens=self.max_tokens, model=model).query(prompt, context)
        extract = re.match(r'<response>(.*?)</response>',outcome, re.DOTALL)
        
        result = extract.group(1).strip() if extract else outcome
        return result
    
    def generate_hyde_content(self, search_string: str, doc_type: str) -> str:
        prompt = self.prompt_manager.get_latest_prompt_template('GroqBriefingSummarizer.generate_hyde_content')
        return self.summarize_with_prompt(prompt, {'search_string': search_string, 'doc_type': doc_type}, model=Models.LLAMA3_8B_8192)