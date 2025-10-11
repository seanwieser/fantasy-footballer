.PHONY: test
.ONESHELL:

run-pre-commit:
	poetry run pre-commit run --all-files

run-local:
	poetry run python3 src/fantasy_footballer/main.py

build:
	docker build -t fantasy_footballer:latest -f ./image/Dockerfile .

up:
	docker run -p 8080:8080 --name fantasy_footballer --env-file ./image/.env fantasy_footballer:latest

down:
	docker container stop fantasy_footballer && docker container rm fantasy_footballer

run-dbt:
	poetry run dbt build --profiles-dir ./dbt/fantasy_footballer --project-dir ./dbt/fantasy_footballer
