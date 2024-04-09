from gpt4all import GPT4All
from library.weaviate import VDB

class LLM:
    def __init__(self, model_name, vdb: VDB):
        self.model = GPT4All(model_name)
        self.vdb = vdb

    def query(self, question, key, context_limit = 5, max_tokens=50):

        context = self.vdb.search(question, key, context_limit)
        
        emails = []
        for o in context.objects:
            emails.append(o.properties['text'])
            
        mail_context = '"' + '"\n\n"'.join(emails) + '"\n\n'

        print("Retrieving" + len(emails) + ' emails')
        print("Context " + mail_context)

        prompt = """
        ### Instruction:
        Question: {}
        Context: {}

        You are a chief of staff for the person asking the question given the context. 
        Please provide a response to the question in no more than 5 sentences. If you do not know the answer,
        please respond with "I do not know the answer to that question."

        ### Response:
        """.format(question, mail_context)

        # print out how many bytes the prompt is
        print("Prompt length: ", len(prompt))
        print("Prompt byte size ", len(prompt.encode('utf-8')))

        return self.model.generate(prompt, max_tokens=max_tokens)
    

class Wizard(LLM) :
    def __init__(self, vdb: VDB):
        super().__init__("wizardlm-13b-v1.2.Q4_0.gguf", vdb)

class Falcon(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("gpt4all-falcon-newbpe-q4_0.gguf", vdb)

class Hermes(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("nous-hermes-llama2-13b.Q4_0.gguf", vdb)
    
