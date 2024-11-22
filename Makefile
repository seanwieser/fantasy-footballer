.PHONY: test
.ONESHELL:

run-pre-commit:
	poetry run pre-commit run --all-files

build:
	docker build -t fantasy_footballer:latest -f ./image/Dockerfile .

up:
	docker run -p 8080:8080 --detach --name fantasy_footballer --env-file ./image/.env -v ./resources:/resources/:rw fantasy_footballer:latest

down:
	docker container stop fantasy_footballer && docker container rm fantasy_footballer

fetch-local:
	cd src/fantasy_footballer && poetry run python3 backend/fetch.py
