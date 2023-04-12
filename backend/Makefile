.PHONY: test
.ONESHELL:

#these 2 next blocks allow passing positional arguments to Make
args = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

%:
    @:

run-pytest:
	poetry run pytest -vvv tests/

# ------------------------------------------------------------------------------------------
#Containerized tools commands

test-image:
	@make -C images test-image