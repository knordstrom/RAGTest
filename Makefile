init:
	poetry install

test:
	poetry run coverage run -m pytest && poetry run coverage report -m

run:
	poetry run flask --app api/main run --port=5010

docker-processor:
	docker build -f ProcessorDockerfile -t context-processor:0.1.1 .
	docker build -f EventProcessorDockerfile -t event-processor:0.1.1 .
