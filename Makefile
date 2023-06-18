.PHONY: test
.ONESHELL:

run-pre-commit:
	pre-commit run --all-files

up:
	docker-compose up --remove-orphans --build -d

down: 
	./scripts/down.sh

build:
	docker-compose build