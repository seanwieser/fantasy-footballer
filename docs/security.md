# Security

How this app handles secrets and sensitive data, and the steps to keep it hardened. Scoped to what
matters for a ~15-person hobby app — see the threat model below.

## Threat model

Optimize for **blast-radius reduction**, not APTs. The realistic risks are a secret leaking (the repo
is **public**; or a laptop / image layer) or the B2 bucket/keys being exposed. Auth passwords are
bcrypt-hashed, so even a full `users.csv` leak doesn't directly surrender passwords — that's the
backstop, so none of this is an emergency.

**Non-goals:** a real secrets manager (Vault/KMS), per-column DB encryption — overkill at this scale.

## Sensitive data

- **Sensitive seeds** (`resources/sensitive_seeds/*.csv`) — owner PII (`owner_names`, `display_names`)
  + bcrypt auth hashes (`users`). The whole `resources/` dir is gitignored; these never go in git.
- **At rest in B2 they are encrypted** (Fernet, keyed by `SEED_ENCRYPTION_KEY`): `write_sensitive_seeds`
  uploads `<name>.csv.enc`; `fetch_resources` decrypts back to plaintext local CSVs at boot (dbt seeds
  read plaintext). The key lives in a different trust boundary than the B2 credentials (a Fly secret /
  local `.envrc` line), so it hardens the "B2 leaked but the app secret didn't" case. Code:
  `backend/encryption.py`, `backend/utils.py`, `backend/db.py`.
- **Local-only files** (`resources/local/`, e.g. iMessage `owner_handles.csv`) never sync to B2 at all.

## Secrets inventory

| Secret | Purpose | Rotate how |
|---|---|---|
| `STORAGE_SECRET` | Signs NiceGUI session cookies (a weak/leaked one lets an attacker forge a logged-in session) | `make rotate-secrets` (auto) |
| `SEED_ENCRYPTION_KEY` | Fernet key encrypting sensitive seeds at rest in B2 | `make rotate-secrets` (auto; re-encrypts + re-pushes seeds) |
| `APPLICATION_KEY_ID` / `APPLICATION_KEY` | B2 bucket access | Backblaze console (manual) |
| `ESPN_S2` / `SWID` | ESPN API cookies | Log in to ESPN in a browser, copy fresh cookies (manual) |
| user auth hashes (`users.csv`) | App login | `/admin` add-user flow (bcrypt) |

## `make rotate-secrets`

One command to rotate the **app-managed** secrets and (re)encrypt the seeds (`scripts/rotate_secrets.py`).
It generates fresh `STORAGE_SECRET` + `SEED_ENCRYPTION_KEY`, rewrites the managed lines in `.envrc`
(and `image/.env` if present) **in place without printing the values**, and re-encrypts + pushes the
sensitive seeds to B2 with the new key. Then it prints the manual follow-ups:

1. `direnv reload` (or re-source `.envrc`) so the new values load into your shell.
2. `./scripts/deploy_app.sh` to push the rotated secrets to Fly.
3. Rotating `STORAGE_SECRET` **invalidates all active sessions** — everyone re-logs in.

Flags: `--dry-run` (print plan, write nothing), `--keys storage,seed` (subset), `--no-push` (skip B2).
First run with no prior `SEED_ENCRYPTION_KEY` is the one-step "turn on seed encryption" path; every
boot thereafter requires the key. It does **not** rotate the provider-managed secrets (B2 keys, ESPN
cookies) — those are manual (see the inventory).

## `make scan-secrets` / gitleaks

`make scan-secrets` runs gitleaks over the full git history (public-repo insurance). A gitleaks
pre-commit hook also blocks new secrets at commit time (and on pre-commit.ci). Known/accepted findings
are allowlisted by fingerprint in `.gitleaksignore`.

**Accepted finding — dead GroupMe token.** A GroupMe API token was hardcoded in `main.py` in a 2023
commit (`369a2d46`, and its pre-commit-ci reformat `62610209`). It is **confirmed dead** (a live API
request returns HTTP 401 — the account/token no longer exists) and is already public in history, so a
history rewrite would buy nothing. It is allowlisted in `.gitleaksignore` and recorded here.

## Owner-operated hardening checklist

These can't be scripted from the app — do them in the provider consoles:

- [ ] **Least-privilege B2 key** — scope the application key to the single bucket, read/write only
      (not the account master key). Biggest bang for the buck. **[done — app uses a bucket-scoped key]**
- [x] **Private bucket** — bucket is set to Private (objects aren't URL-fetchable without auth).
- [ ] **Purge stale B2 partitions** — old date-partitioned uploads (incl. legacy pre-encryption
      plaintext seeds) linger forever. A Backblaze age-based lifecycle rule doesn't fit: each push is a
      new file path, not a version, and pushes are rare, so "delete after N days" could remove the live
      copy. Tracked as **FF-021** (a `make` purge command with explicit keep-latest logic).
- [ ] **Fly secrets, not image-baked env** — set prod secrets via `fly secrets set` (or
      `./scripts/deploy_app.sh`); keep them out of image layers / `image/.env`. (Prod isn't properly
      set up yet — see **FF-004**.)
- [x] **Strong `STORAGE_SECRET` + `SEED_ENCRYPTION_KEY`** — rotate via `make rotate-secrets`.
- [ ] **Rotate ESPN cookies** — re-pull from a browser when ingestion auth starts failing (no fixed
      cadence; the cookies are ESPN-issued).
- [x] **gitleaks history scan** — `make scan-secrets` returns clean.
