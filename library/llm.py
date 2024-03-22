from gpt4all import GPT4All
from library.weaviate import VDB

class LLM:
    def __init__(self, model_name, vdb: VDB):
        self.model = GPT4All(model_name)
        self.vdb = vdb

    def query(self, question, max_tokens=50):

        print("Asking   : ", question)
        context = self.vdb.search(question)
        
        print("Context  : ", str(context))
        
        # .join(" | ")

        prompt = """
        Question: {}
        Email Context: {}

        You are a chief of staff for the person asking the question given the context above. 
        Please provide a response to the question in no more than 5 sentences. If you do not know the answer,
        please respond with "I do not know the answer to that question."
        """.format(question, context)

        return self.model.generate(prompt, max_tokens=max_tokens)
    

class Wizard(LLM) :
    def __init__(self, vdb: VDB):
        super().__init__("wizardlm-13b-v1.2.Q4_0.gguf", vdb)
    
