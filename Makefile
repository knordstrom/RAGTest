init:
	poetry install

test:
	poetry run coverage run -m pytest tests/unit/ && poetry run coverage report -m

test-it:
	poetry run coverage run -m pytest tests/integration/ && poetry run coverage report -m

test-all:
	poetry run coverage run -m pytest tests/ && poetry run coverage report -m

run:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 5010

docker-processor:
	docker build -f ProcessorDockerfile -t context-processor:0.1.1 .
	docker build -f EventProcessorDockerfile -t event-processor:0.1.1 .
	docker build -f DocumentProcessorDockerfile -t document-processor:0.1.1 .

docker-api:
	docker build -f ApiDockerfile -t context-api:0.1.1 .

docker-all: 
	make docker-processor 
	make docker-api
