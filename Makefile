.PHONY: test
.ONESHELL:

run-pre-commit:
	pre-commit run --all-files

build:
	docker-compose build

up:
	docker-compose up --remove-orphans