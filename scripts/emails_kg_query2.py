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
import logging

openai_apikey = "add_key_here"
url = "bolt://localhost:7687" #default
username = "neo4j" #default username unless changed
password = "add_password_here"
graph = Neo4jGraph(url=url, username=username, password=password)

llm = ChatOpenAI(temperature=0, model_name="gpt-4-0125-preview", openai_api_key=openai_apikey)

# Detecting entities in the user input
# We have to extract the types of entities/values we want to map to a graph database. 
# In this example, we are dealing with a email chain graph, so we can map meetings, documents
# and people to the database.

class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the persons, documents, events or dates appearing in the text",
    )


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting persons, documents, events or dates from the text.",
        ),
        (
            "human",
            "Use the given format to extract information from the following "
            "input: {question}",
        ),
    ]
)


entity_chain = create_structured_output_chain(Entities, llm, prompt)

## testing out if this entity chain works
# that is, testing out if entities are being extracted from the query

entities = entity_chain.invoke({"question": "Who is attending the Kickoff Meeting?"})
print("entities: ", entities)

match_query = """MATCH (p:Person|Document|Event|Date)
WHERE p.id CONTAINS $value
RETURN coalesce(p.id) AS result, labels(p)[0] AS type
LIMIT 1
"""


def map_to_database(values):
    result = ""
    for entity in values.names:
        response = graph.query(match_query, {"value": entity})
        try:
            result += f"{entity} maps to {response[0]['result']} {response[0]['type']} in database\n"
        except IndexError:
            pass
    return result

## check if this map_to_database function works
res = map_to_database(entities["function"])
print("map_to_database function returned: ", res)


# Custom Cypher generating chain
# We need to define a custom Cypher prompt that takes the entity mapping information along with the schema 
# and the user question to construct a Cypher statement. 
# We will be using the LangChain expression language to accomplish that.

# Generate Cypher statement based on natural language input
cypher_template = """Based on the Neo4j graph schema below, write a Cypher query that would answer the user's question:
{schema}
Entities in the question map to the following database values:
{entities_list}
Question: {question}
Cypher query:"""  # noqa: E501
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



cypher_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given an input question, convert it to a Cypher query without markdown elements. No pre-amble.",
        ),
        ("human", cypher_template),
    ]
)


cypher_response = (
    RunnablePassthrough.assign(names=entity_chain)
    | RunnablePassthrough.assign(
        entities_list=lambda x: map_to_database(x["names"]["function"]),
        schema=lambda _: graph.get_schema,
    )
    | cypher_prompt
    | llm.bind(stop=["\nCypherResult:"])
    | StrOutputParser()
)

cypher = cypher_response.invoke({"question": "Who is the organizer of the Kickoff Meeting?"})
cleaned_cypher = cypher.strip('`').strip('cypher').strip()
print("cypher: ", cleaned_cypher)

# Generating answers based on database results
# Now that we have a chain that generates the Cypher statement, we need to execute the Cypher statement 
# against the database and send the database results back to an LLM to generate the final answer. 
# Again, we will be using LCEL.

# Cypher validation tool for relationship directions
corrector_schema = [
    Schema(el["start"], el["type"], el["end"])
    for el in graph.structured_schema.get("relationships")
]
cypher_validation = CypherQueryCorrector(corrector_schema)

# Generate natural language response based on database results
response_template = """Based on the the question, Cypher query, and Cypher response, write a natural language response:
Question: {question}
Cypher query: {query}
Cypher Response: {response}"""  # noqa: E501

try:
    response_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Given an input question and Cypher response, convert it to a natural"
                " language answer. No pre-amble.",
            ),
            ("human", response_template),
        ]
    )

    chain = (
        RunnablePassthrough.assign(query=cypher_response)
        | RunnablePassthrough.assign(
            response=lambda x: graph.query(cypher_validation(x["query"])),
        )
        | response_prompt
        | llm
        | StrOutputParser()
    )
    result = chain.invoke({"question": "Who is the organizer of the Kickoff Meeting?"})
    print("result: ", result)
except Exception as e:
        logging.error("Failed to process chain: %s", e)


