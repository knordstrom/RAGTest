init:
	pip install -r requirements.txt

test:
	poetry run coverage run -m pytest && poetry run coverage report -m
