from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from library.weaviate import VDB
from langchain.chains.llm import LLMChain
from langchain_community.llms import GPT4All
from langchain import PromptTemplate

class LLM:
    def __init__(self, model_name, vdb: VDB):
        callbacks = [StreamingStdOutCallbackHandler()]
        self.model = GPT4All(model=model_name, callbacks=callbacks, verbose=True)
        self.vdb = vdb

    def query(self, question, key, context_limit = 5, max_tokens=500):

        context = self.vdb.search(question, key, context_limit)
        
        emails = []
        for o in context.objects:
            emails.append(o.properties['text'])
            
        mail_context = '"' + '"\n\n"'.join(emails) + '"\n\n'

        print("Retrieving" + str(len(emails)) + ' emails')
        print("Context " + mail_context)

        # LANGCHAIN IMPLEMENTATION
        template='''### Instruction:
        Question: {Question}
        Context: {Context}

        You are a chief of staff for the person asking the question given the context. 
        Please provide a response to the question in no more than 5 sentences. If you do not know the answer,
        please respond with "I do not know the answer to that question."

        ### Response:'''
        
        return self.query_with_template(template, {'Question': question, 'Context':mail_context})
        
    
    def query_with_template(self, template: str, config: dict, context_limit = 5, max_tokens=500, prompt=None):

        language_prompt = PromptTemplate(
            input_variables=list(config.keys()),
            template=template,
        )

        # print out how many bytes the prompt is
        print("Prompt length: ", len(template))
        print("Prompt byte size ", len(template.encode('utf-8')))

        llm_chain = LLMChain(prompt=language_prompt, llm=self.model.llm)
        response = llm_chain(config)
        
        print("Response: ", response)
        return response

class Wizard(LLM) :
    def __init__(self, vdb: VDB):
        super().__init__("wizardlm-13b-v1.2.Q4_0.gguf", vdb)

class Falcon(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("gpt4all-falcon-newbpe-q4_0.gguf", vdb)

class Hermes(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("nous-hermes-llama2-13b.Q4_0.gguf", vdb)

class Mini(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("all-MiniLM-L6-v2-f16.gguf", vdb)        

class MistralOrca(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("mistral-7b-openorca.gguf2.Q4_0.gguf", vdb)   
    
class MistralInstruct(LLM):
    def __init__(self, vdb: VDB):
        super().__init__("mistral-7b-instruct-v0.1.Q4_0.gguf", vdb)   


        

    
