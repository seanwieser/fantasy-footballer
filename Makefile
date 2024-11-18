.PHONY: test
.ONESHELL:

run-pre-commit:
	poetry run pre-commit run --all-files

build:
	docker build -t fantasy_footballer:latest -f ./image/Dockerfile .

run:
	docker run --env-file ./image/.env -v ./resources:/resources/:rw fantasy_footballer:latest

fetch-local:
	cd src/fantasy_footballer && poetry run python3 backend/fetch.py
