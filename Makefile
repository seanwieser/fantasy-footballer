.PHONY: test
.ONESHELL:

FORMAT ?= table

run-pre-commit:
	poetry run pre-commit run --all-files

run-local-fresh:
	poetry run python3 src/fantasy_footballer/main.py

run-local-dev:
	poetry run python3 src/fantasy_footballer/main.py --dev-mode

build:
	docker build -t fantasy_footballer:latest -f ./image/Dockerfile .

up:
	docker run -p 8080:8080 --name fantasy_footballer --env-file ./image/.env fantasy_footballer:latest

down:
	docker container stop fantasy_footballer && docker container rm fantasy_footballer

run-dbt:
	./scripts/run_dbt_local.sh

# Local-only s003 iMessage extract → B2 (code in scripts/imessage/). Owner-operated; needs Full Disk
# Access, the imessage-exporter binary, and `poetry install --with imessage`. -full purges B2 and
# re-exports all history (first run / rebuild); extract-imessage adds an incremental slice.
extract-imessage:
	PYTHONPATH=src/fantasy_footballer:scripts poetry run python3 -m imessage

extract-imessage-full:
	PYTHONPATH=src/fantasy_footballer:scripts poetry run python3 -m imessage --full

purge-imessage:
	PYTHONPATH=src/fantasy_footballer:scripts poetry run python3 -m imessage --purge

# Upload local sensitive seeds (resources/sensitive_seeds/*.csv) to B2 under today's date partition.
# Run from repo root so the relative resources/ path resolves; needs B2 creds + SEED_ENCRYPTION_KEY
# (.envrc) loaded. Seeds are encrypted at rest in B2 (decrypted at boot by fetch_resources).
push-sensitive-seeds:
	PYTHONPATH=src/fantasy_footballer poetry run python3 -c "from backend.utils import write_sensitive_seeds; write_sensitive_seeds()"

# Rotate the app-managed secrets (STORAGE_SECRET, SEED_ENCRYPTION_KEY), rewrite the local env files,
# and re-encrypt + push the sensitive seeds to B2. Owner-operated. Pass flags via ARGS, e.g.
# `make rotate-secrets ARGS=--dry-run` or `ARGS="--keys seed --no-push"`.
rotate-secrets:
	PYTHONPATH=src/fantasy_footballer poetry run python3 scripts/rotate_secrets.py $(ARGS)

# Scan the full git history for committed secrets (public-repo insurance). Allowlist in .gitleaksignore.
scan-secrets:
	gitleaks detect --source . --redact --no-banner

query:
	poetry run python3 scripts/query_db.py --format $(FORMAT) "$(SQL)"