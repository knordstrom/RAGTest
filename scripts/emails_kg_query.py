from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain


openai_apikey = "add_key_here"
url = "bolt://localhost:7687" #default
username = "neo4j" #default username unless changed
password = "add_password_here"
graph = Neo4jGraph(url=url, username=username, password=password)

llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_apikey)

chain = GraphCypherQAChain.from_llm(graph=graph, llm=llm, verbose=True, validate_cypher=True)
response = chain.invoke({"query": "Who are the people attending the kickoff meeting?"})

print(response)