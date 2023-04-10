.PHONY: test
.ONESHELL:

#these 2 next blocks allow passing positional arguments to Make
args = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

%:
    @:

run-pytest:
	poetry run pytest -vvv tests/

run-pre-commit:
	poetry run pre-commit run --all-files;

# ------------------------------------------------------------------------------------------
#Containerized tools commands

build-image:
	@make -C images build-image

test-image: build-image
	@make -C images test-image