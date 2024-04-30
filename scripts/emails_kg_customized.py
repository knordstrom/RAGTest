from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document

## This didn't really work out because it would try to match the EXACT word I gave in the entities and 
## relationships and would obviously not find that in the email - hence pivoting to embeddings

openai_apikey = "add_key_here"
url = "bolt://localhost:7687" #default
username = "neo4j" #default username unless changed
password = "add_password_here"
graph = Neo4jGraph(url=url, username=username, password=password)

llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_apikey)

llm_transformer_filtered = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=[
    "Person", "Group", "Position", "Location", "Institution", "Event", "Initiative", "Document",
    "Task", "Meeting", "Product", "Service", "Deadline", "Department", "Campaign", "Policy", "Technology",
    "Issue", "Solution"
    ],
    allowed_relationships=[
    "is located at", "participates in", "makes requests", "responds to requests", "writes", "edits", 
    "comments on", "belongs to", "holds", "has applied for", "contacted", "has title", "visited", "located in",
    "is filled by", "works for", "is offered by", "employs", "affiliates with", "hires", "houses", 
    "sponsors", "hires for", "reports to", "collaborates with", "approves", "rejects", "attends", "hosts", 
    "schedules", "submits", "reviews", "requires", "assigns", "shares", "mentions", "relates to", "updates", 
    "follows up on", "leads"
    ]
)

text = """
Hi Emily,

I'll be there. I've started compiling the marketing data for the quarter and have some insights to share that could impact our overall strategy.

Best,
Tom
"""
documents = [Document(page_content=text)]
graph_documents = llm_transformer_filtered.convert_to_graph_documents(documents)
print(f"Nodes:{graph_documents[0].nodes}")
print(f"Relationships:{graph_documents[0].relationships}")

graph.add_graph_documents(graph_documents)