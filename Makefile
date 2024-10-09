init:
	poetry install

test:
	poetry run coverage run -m pytest tests/unit/ && poetry run coverage lcov

test-it:
	poetry run coverage run -m pytest tests/integration/ && poetry run coverage lcov

test-all:
	poetry run coverage run -m pytest tests/ && poetry run coverage lcov

run:
	uvicorn api.main:app --reload --reload-exclude processor --host 0.0.0.0 --port 5010

run-fake:
	uvicorn api_fake.main:app --reload --reload-exclude processor --host 0.0.0.0 --port 5010

docker-processor:
	docker build -f EmailProcessorDockerfile -t context-processor:0.1.1 .
	docker build -f EventProcessorDockerfile -t event-processor:0.1.1 .
	docker build -f DocumentProcessorDockerfile -t document-processor:0.1.1 .
	docker build -f TranscriptProcessorDockerfile -t transcript-processor:0.1.1 .
	docker build -f SlackProcessorDockerfile -t slack-processor:0.1.1 .

docker-api:
	docker build -f ApiDockerfile -t context-api:0.1.1 .

docker-all: 
	make docker-processor 
	make docker-api
	docker image tag context-processor:0.1.1 knordstrom/email-processor:$(VERSION)
	docker image tag event-processor:0.1.1 knordstrom/event-processor:$(VERSION)
	docker image tag document-processor:0.1.1 knordstrom/document-processor:$(VERSION)
	docker image tag transcript-processor:0.1.1 knordstrom/transcript-processor:$(VERSION) 
	docker image tag slack-processor:0.1.1 knordstrom/slack-processor:$(VERSION)
	docker image tag context-api:0.1.1 knordstrom/sofia-api:$(VERSION)
	docker push knordstrom/email-processor:$(VERSION)
	docker push knordstrom/event-processor:$(VERSION)
	docker push knordstrom/document-processor:$(VERSION)
	docker push knordstrom/transcript-processor:$(VERSION)
	docker push knordstrom/slack-processor:$(VERSION)
	docker push knordstrom/sofia-api:$(VERSION)

