.PHONY: test
.ONESHELL:

args = `arg="$(filter-out $@,$(MAKECMDGOALS))" && echo $${arg:-${1}}`

# We want regular linux arch when deploying images, running on Mac uses arm64 arch by default
# we run the build from root directory so the root package can be installed
build-image:
	cd .. && docker build  --platform linux/x86_64 -t $(image) -f images/$(image)/image/Dockerfile .

test-image:
	@bash $(image)/tests/run_image_tests.sh