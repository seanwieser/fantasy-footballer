.PHONY: test
.ONESHELL:

run-pre-commit:
	pre-commit run --all-files