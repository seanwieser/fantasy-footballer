.PHONY: test
.ONESHELL:

args = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

test-image:
	@bash $(image)/tests/run_image_tests.sh