"""
Rotate the app-managed secrets and (re)encrypt the sensitive seeds in one step.

Run via `make rotate-secrets` (owner-operated — it rewrites local `.envrc` and pushes to B2).

It rotates the two secrets the app fully controls (`STORAGE_SECRET`, `SEED_ENCRYPTION_KEY`),
writes the fresh values into the local env files in place (never echoing them), and re-encrypts +
pushes the sensitive seeds to B2 with the new encryption key. Provider-owned secrets (B2 keys, ESPN
cookies, user auth hashes) can't be scripted — the script prints how to rotate those by hand.
"""
import argparse
import os
import re
import secrets
import sys

from backend.encryption import generate_key
from backend.utils import write_sensitive_seeds

# var -> human label, for the index table.
APP_MANAGED = {
    "storage": ("STORAGE_SECRET", "NiceGUI session-cookie signing key"),
    "seed": ("SEED_ENCRYPTION_KEY", "Fernet key for sensitive seeds at rest in B2"),
}

PROVIDER_MANAGED = [
    ("APPLICATION_KEY_ID / APPLICATION_KEY", "Backblaze console — scope a new app key to the one bucket"),
    ("ESPN_S2 / SWID", "Log in to ESPN in a browser and copy the fresh cookies"),
    ("user auth hashes (users.csv)", "Use the /admin 'add user' flow (bcrypt-rehashes)"),
]

ENV_FILES = [
    (".envrc", "export "),   # local direnv file: `export VAR='...'`
    ("image/.env", ""),      # docker env-file: `VAR='...'`
]


def _print_index(selected):
    """Print the secret inventory: what this run rotates vs. what must be rotated by hand."""
    print("Secret rotation index")
    print("  App-managed (rotated by this tool):")
    for key, (var, label) in APP_MANAGED.items():
        mark = "rotate" if key in selected else "skip"
        print(f"    [{mark:>6}] {var:<22} {label}")
    print("  Provider-managed (manual — not scripted):")
    for var, how in PROVIDER_MANAGED:
        print(f"    [manual] {var:<22} {how}")
    print()


def _update_env_file(path, prefix, updates, dry_run):
    """Replace each `{prefix}VAR=...` line in `path` (appending if absent); never print values."""
    if not os.path.exists(path):
        print(f"  - {path}: not present, skipped")
        return
    with open(path, "r", encoding="utf-8") as env_file:
        lines = env_file.read().splitlines()

    for var, value in updates.items():
        new_line = f"{prefix}{var}='{value}'"
        pattern = re.compile(rf"^{re.escape(prefix)}{re.escape(var)}=.*$")
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = new_line
                break
        else:
            lines.append(new_line)

    if dry_run:
        print(f"  - {path}: would update {', '.join(updates)} (dry-run, not written)")
        return
    with open(path, "w", encoding="utf-8") as env_file:
        env_file.write("\n".join(lines) + "\n")
    print(f"  - {path}: updated {', '.join(updates)}")


def main():
    """Generate fresh app secrets, persist them locally, and re-encrypt + push the seeds."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keys", default="storage,seed",
                        help="comma list of app-managed keys to rotate (storage,seed). Default: both.")
    parser.add_argument("--no-push", action="store_true",
                        help="skip re-encrypting + pushing seeds to B2.")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the planned actions without writing files or pushing to B2.")
    args = parser.parse_args()

    selected = {k.strip() for k in args.keys.split(",") if k.strip()}
    unknown = selected - set(APP_MANAGED)
    if unknown:
        parser.error(f"unknown keys: {', '.join(sorted(unknown))}. Valid: {', '.join(APP_MANAGED)}")

    _print_index(selected)

    new_values = {}
    if "storage" in selected:
        new_values["STORAGE_SECRET"] = secrets.token_urlsafe(48)
    new_seed_key = None
    if "seed" in selected:
        new_seed_key = generate_key()
        new_values["SEED_ENCRYPTION_KEY"] = new_seed_key

    print("Writing local env files:" if not args.dry_run else "Planned local env-file changes:")
    for path, prefix in ENV_FILES:
        _update_env_file(path, prefix, new_values, args.dry_run)
    print()

    # Re-encrypting with the new key in-process is mandatory whenever the seed key rotated, otherwise
    # the existing B2 ciphertext (encrypted under the old key) can no longer be decrypted at boot.
    if args.no_push:
        if new_seed_key:
            print("WARNING: --no-push with a rotated SEED_ENCRYPTION_KEY — existing B2 seeds can no "
                  "longer be decrypted until you push. Re-run without --no-push.")
    elif args.dry_run:
        print("Would re-encrypt and push sensitive seeds to B2 (dry-run, skipped).\n")
    else:
        print("Re-encrypting and pushing sensitive seeds to B2...")
        write_sensitive_seeds(encryption_key=new_seed_key)
        print("  - pushed encrypted seeds under today's date partition.\n")

    print("Next steps (manual):")
    print("  1. `direnv reload` (or re-source .envrc) so the new values load into your shell.")
    print("  2. `./scripts/deploy_app.sh` to push the rotated secrets to Fly.")
    if "storage" in selected:
        print("  3. NOTE: rotating STORAGE_SECRET invalidates all active sessions — everyone re-logs in.")
    if args.dry_run:
        print("\n(dry-run: nothing was written or pushed.)")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
