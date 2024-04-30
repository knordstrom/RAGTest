from typing import List, Optional
from langchain.chains.openai_functions import create_structured_output_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.neo4j_vector import Neo4jVector
import os

openai_apikey = "add_key_here"
url = "bolt://localhost:7687" #default
username = "neo4j" #default username unless changed
password = "add_password_here"
graph = Neo4jGraph(url=url, username=username, password=password)

llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_apikey)
llm_transformer = LLMGraphTransformer(llm=llm)

# embedding model
embeddings_model = "text-embedding-3-small"  # Or another model like "text-davinci-003" for embeddings

entities_list = ['Concept', 'Data', 'Date', 'Document', 'Event', 'Group', 'Person', 'Report']
email_folder = 'emails'  # Folder where your email files are stored

for i in range(1, 11):  # Assuming you have 10 emails, labeled email1.txt to email10.txt
    file_path = os.path.join(email_folder, f'email{i}.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            documents = [Document(page_content=text)]
            graph_documents = llm_transformer.convert_to_graph_documents(documents)
            print(f'Processing {file_path}')
            print(f"Nodes: {graph_documents[0].nodes}")
            print(f"Relationships: {graph_documents[0].relationships}")

            graph.add_graph_documents(graph_documents)
    except Exception as e:
        print(f"Failed to process {file_path}: {str(e)}")

def embed_entities(entity_type):
    vector_index = Neo4jVector.from_existing_graph(
        OpenAIEmbeddings(model=embeddings_model,openai_api_key=openai_apikey),
        url=url,
        username=username,
        password=password,
        index_name=entity_type,
        node_label=entity_type,
        text_node_properties=['id'],
        embedding_node_property='embedding',
    )
    

for t in entities_list:
    embed_entities(t)
# Querying the database
# Creating vector indexes
# In order to efficiently search our database for terms closely related to user queries, we need to use embeddings. 
# To do this, we will create vector indexes on each type of property - in this case, the only property we have
# is "id" which is the same as the name of the entity.

# We will be using the OpenAIEmbeddings Langchain utility. 
# It's important to note that Langchain adds a pre-processing step, so the embeddings will slightly differ 
# from those generated directly with the OpenAI embeddings API.