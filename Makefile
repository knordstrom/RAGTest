init:
	pip install -r requirements.txt

test:
	poetry run pytest

run:
	flask --app api/main run --port=5010
