from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

openai_apikey = "add_key_here"
url = "bolt://localhost:7687" #default
username = "neo4j" #default username unless changed
password = "add_password_here"
graph = Neo4jGraph(url=url, username=username, password=password)

llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_apikey)

llm_transformer = LLMGraphTransformer(llm=llm)

text = """
Team,

Thank you for a productive meeting today. I appreciate everyone's insights and contributions. Please proceed with the actions discussed, and let's aim to have the draft report ready for review by next Wednesday. Feel free to reach out if you encounter any issues.

Best regards,
Emily
"""
documents = [Document(page_content=text)]
graph_documents = llm_transformer.convert_to_graph_documents(documents)
print(f"Nodes:{graph_documents[0].nodes}")
print(f"Relationships:{graph_documents[0].relationships}")

graph.add_graph_documents(graph_documents)