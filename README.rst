#RAG Test
========================

This is a very basic test repo using GPT4All, Weaviate, and a gmail account in order to answer questions through a flask API.

## Setup

1. Clone the repo
2. Install the requirements
3. Install docker desktop that will house the weaviate server
4. Navigate to docker/weaviate and run `docker-compose up -d` to start the weaviate server
5. Download credentials from the google cloud console at https://console.cloud.google.com/apis/credentials and place them in the `resources` folder as `gmail_creds.json`
6, Run the flask app with `flask --app api/main run --port=5010`

## Usage

### Populate Weaviate

1. Issue a GET request to `http://localhost:5010/email?e=[YOUR EMAIL ADDRESS HERE]` to populate the weaviate server with your most recent gmail entries

### Query the LLM

1. Issue a GET request to `http://localhost:5010/ask?q=[YOUR QUESTION HERE]` to query the LLM model and your existing emails with your question

### Run tests

1. Run `pytest` in the root directory using `poetry run pytest` (or `make test` if you have `make` installed)