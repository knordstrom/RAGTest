

RAG Test
========================

.. |testing| image:: https://github.com/knordstrom/RAGTest/actions/workflows/unit-testing.yml/badge.svg
   :alt: Unit tests
.. |coverage| image:: https://coveralls.io/repos/github/knordstrom/RAGTest/badge.svg?branch=main
   :target: https://coveralls.io/github/knordstrom/RAGTest?branch=main&v=0.0.21

|testing| |coverage|

This is a basic test repo using Groq, Neo4j, Weaviate, and some data accounts (GSuite, Slack) in order to answer questions 
through a FastAPI API. Emails are read from the gmail account according to parameters sent to the API then 
sent through a Kafka topic to a processor that vectorizes and stores them. A separate API then allows a question 
to be asked with a certain number of emails to be retrieved and used to answer the question, or for proactive briefs to be preesented 
based on a GSuite schedule and a given time range.

Note the performance of this second endpoint is weak because too much context is required to answer the question 
relative to the size of the text in the emails. The step towards solving this is the next phase, in which we will
preprocess email content into a Neo4j knowledege graph and use that to answer questions.

Setup
-----

  #. Clone the repo
  #. Install the requirements using `make init` or `poetry install`
  #. Get an API key for Groq at https://console.groq.com/keys 
  #. Add it as `GROQ_API_KEY` in a `.env` file in the `docker` directory
  #. Install docker desktop that will house the weaviate server
  #. Run `make docker-processor` in the root folder to create the container to process emails
  #. Navigate to the docker folder and run `docker-compose up -d` to start the weaviate server, kafka, zookeeper, and the processor
  #. Download credentials from the google cloud console at https://console.cloud.google.com/apis/credentials and place them in the `resources` folder as `gmail_creds.json`
  #. Set your GROQ key as an environment variable `GROQ_API_KEY`. You can also do this through a .env file in the root folder of the project
  #. Run the FastAPI app with `make run` or `uvicorn api.main:app --reload --host 0.0.0.0 --port 5010` 
  #. Follow the temporary instructions for downloading conversations from slack's API and storing them in the weaviate server (see below under Slack)

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

Slack
^^^^^

Leveraging the slack API to retrieve conversational context requires management of multiple tokens and thus, at the moment, a bit of manual work, as 
handling multiple hand-rolled refresh token and token storage processes is out of scope for this POC. Slack's API also requires a valid https endpoint to
receive token requests, so the process is a bit more involved than the gmail API.

For the near future, this means that only people with access to a slack app being used will be able to use slack conversations. Steps:

  #. In order to set up an https proxy, use ngrok:
    #. Follow instructions at https://ngrok.com/docs/guides/getting-started/
    #. Login to the slack apps console at https://api.slack.com/apps
  #. Visit https://127.0.0.1:5010/slack, which will forward you to authenticate with slack
  #. This will take you through an OAuth flow in which you will acknowledge the permissions the app is requesting
  #. However, due to the fact the code currently handles the "bot" token incorrectly, it is probably you will need to visit the app's settings in the slack API console 
    #. Both tokens are available for copy in the interface exposed by slack under "OAuth & Permissions"
    #. Copy the "bot" token and paste it into the `access_token` property `slack_bot_token.json` file that should be created in the root folder of this project
    #. You should also update the expiration date in the `slack_bot_token.json` file to the date being proposed in the slack settings
  #. If you have further problems with auth, the "user" token is also available in the slack app settings
  #. Once auth is ironed out, make another request to https://127.0.0.1:5010/slack to retrieve the conversations
  #. Run `python processor/slack_processor.py` from the command line in the root directory to process the conversations and store them in weaviate
