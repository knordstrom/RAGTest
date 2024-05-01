## Information about the Python Notebooks

The Python Notebooks are categorized into two groups. Most of the code is derived from the LangChain Documentation on [Graphs](https://python.langchain.com/docs/use_cases/graph/):

1. **Creation of the Knowledge Graph (KG) Using Email Data:**
    - `emails_kg.ipynb`: This script offers a basic approach to creating the KG. It connects to a Neo4j graph database configured using Neo4j Desktop and utilizes OpenAI's LLMGraphTransformer to extract entities and relationships from a block of text.
    - `emails_kg_customized.ipynb`: This script specifies `allowed_entities` and `allowed_relationships` as parameters in the LLMGraphTransformer. It attempts to extract entities and relationships based on these lists. However, it struggles to find exact matches, resulting in many missed relationships.
    - `emails_kg_vectorized.ipynb`: This script creates a KG and adds embeddings for the entities. Currently, the only property of these entities is "id," which represents the name of the entity (e.g., if the entity is Person:Katie, then id = "Katie"). The script creates an embedding for the id and stores this embedding as a property of the entity called "embedding."

2. **Querying the KG:**
    - `emails_kg_query.ipynb`: This file uses a straightforward method for querying the Neo4j graph. It employs the GraphCypherQAChain from LangChain, which converts a natural language query into a Cypher query and returns the result in natural language. All intermediate steps are abstracted by this method.
    - `emails_kg_query2.ipynb`: This script introduces additional complexity by extracting entities from the query based on a prompt and predefined entities. It then maps these to a database entity, creates a Cypher query, and returns the result as a Cypher response. This response is subsequently converted back into natural language. Further enhancements include using cosine similarity and vectorizing the query as specified in this [OpenAI Cookbook](https://cookbook.openai.com/examples/rag_with_graph_db).

## Running These Python Files:
1. Create a project and database on Neo4j, then start it. Update the script with your database's URL, username, and password.
2. Obtain an OpenAI API key and configure it in the script.
3. Execute the cells in the notebook

