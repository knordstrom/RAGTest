RAG Test
========================

This is a very basic test repo using GPT4All, Weaviate, and a gmail account in order to answer questions 
through a flask API. Emails are read from the gmail account according to parameters sent to the API then 
sent through a Kafka topic to a processor that vectorizes and stores them. A separate API then allows a question 
to be asked with a certain number of emails to be retrieved and used to answer the question.

Note the performance of this second endpoint is weak because too much context is required to answer the question 
relative to the size of the text in the emails. The step towards solving this is the next phase, in which we will
preprocess email content into a Neo4j knowledege graph and use that to answer questions.

Setup
-----

  #. Clone the repo
  #. Install the requirements using `make init` or `poetry install`
  #. Install docker desktop that will house the weaviate server
  #. Run `make docker-processor` in the root folder to create the container to process emails
  #. Navigate to the docker folder and run `docker-compose up -d` to start the weaviate server, kafka, zookeeper, and the processor
  #. Download credentials from the google cloud console at https://console.cloud.google.com/apis/credentials and place them in the `resources` folder as `gmail_creds.json`
  #. Run the flask app with `make run` or `flask --app api/main run --port=5010`

Usage
-----

Populate Weaviate
^^^^^^^^^^^^^^^^^

  *. Issue a GET request to `http://localhost:5010/email?e=[YOUR EMAIL ADDRESS HERE]&n=[COUNT_OF_EMAILS_TO_RETRIEVE]` to populate the weaviate server with your most recent gmail entries

Query the LLM
^^^^^^^^^^^^^

  *. Issue a GET request to `http://localhost:5010/ask?q=[YOUR QUESTION HERE]` to query the LLM model and your existing emails with your question

Run tests
^^^^^^^^^

  *. Run `pytest` in the root directory using `make test` or `poetry run pytest`
