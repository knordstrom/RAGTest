from groq import Groq


class GroqClient:

    def __init__(self, key, model = "llama3-70b-8192", temperature=0.01, max_tokens=2000):
        self.key = key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = Groq(
            api_key=key
        )

    def query(self, prompt, context):
        print(prompt.format(**context))
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