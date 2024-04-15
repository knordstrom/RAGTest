RAG Test
========================

This is a very basic test repo using GPT4All, Weaviate, and a gmail account in order to answer questions through a flask API.

Setup
-----

  #. Clone the repo
  #. Install the requirements using `make init` or `poetry install`
  #. Install docker desktop that will house the weaviate server
  #. Navigate to the docker/weaviate folder and run `docker-compose up -d` to start the weaviate server
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
