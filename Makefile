init:
	poetry install

test:
	poetry run coverage run -m pytest && poetry run coverage report -m

run:
	poetry run flask --app api/main run --port=5010
