.PHONY: test
.ONESHELL:

run-pre-commit:
	poetry run pre-commit run --all-files

build:
	docker build -t fantasy_footballer:latest -f ./image/Dockerfile .

run:
	docker run --network="host" --env-file ./image/.env -v ./resources:/resources/:rw fantasy_footballer:latest -p 8080:8080/tcp

fetch-local:
	cd src/fantasy_footballer && poetry run python3 backend/fetch.py
