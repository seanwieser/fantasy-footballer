"""
Symmetric encryption for sensitive seeds at rest in B2.

Owner PII + bcrypt auth hashes live in ``resources/sensitive_seeds/*.csv``. Locally these stay
plaintext (dbt seeds read them directly); only the copies pushed to B2 are encrypted, keyed by the
``SEED_ENCRYPTION_KEY`` env var (a Fernet key). The key lives in a different trust boundary than the
B2 bucket credentials (a Fly secret / local ``.envrc`` line), so it hardens the "B2 leaked but the
app secret didn't" case. There is no plaintext fallback — a missing key is a hard error.
"""
import os

from cryptography.fernet import Fernet

SEED_ENCRYPTION_KEY_ENV = "SEED_ENCRYPTION_KEY"


def generate_key() -> str:
    """Return a fresh urlsafe-base64 Fernet key as a string."""
    return Fernet.generate_key().decode("utf-8")


def _resolve_key(key=None) -> bytes:
    """Resolve the Fernet key from the explicit arg or the env var; raise if neither is set."""
    key = key or os.getenv(SEED_ENCRYPTION_KEY_ENV)
    if not key:
        raise RuntimeError(
            f"{SEED_ENCRYPTION_KEY_ENV} is not set. Run `make rotate-secrets` to generate one "
            "and encrypt the sensitive seeds."
        )
    return key.encode("utf-8") if isinstance(key, str) else key


def encrypt_bytes(data: bytes, key=None) -> bytes:
    """Encrypt raw bytes with the resolved Fernet key."""
    return Fernet(_resolve_key(key)).encrypt(data)


def decrypt_bytes(token: bytes, key=None) -> bytes:
    """Decrypt a Fernet token back to raw bytes with the resolved key."""
    return Fernet(_resolve_key(key)).decrypt(token)
