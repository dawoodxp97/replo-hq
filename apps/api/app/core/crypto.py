"""Authenticated encryption for BYOK credentials.

AES-256-GCM. This module is the **only** place a user's API key exists in
plaintext outside the outbound HTTP request that uses it.

## Why AAD matters here

Every ciphertext is bound to `"{user_id}:{provider}"` as additional authenticated
data. AAD is not encrypted — it is *authenticated*, meaning decryption fails
unless the same value is supplied again.

Concretely: if someone with database write access copies a `ciphertext`/`nonce`
pair from Alice's row into Bob's, decryption fails instead of handing Bob a
working key billed to Alice. Without AAD, the ciphertext would be portable
between rows and that attack would succeed. It also means a row cannot be
silently re-pointed at a different provider.

## Key rotation

`key_version` is stored per row. `credential_encryption_key_previous` lets both
keys decrypt during a rotation window while new writes use the current key. No
row is ever stranded by a rotation.

## Failure mode

Decryption failures raise `CredentialDecryptionError` and never fall back to a
partial result. A credential that cannot be decrypted is treated as absent —
degrading to "no key" is correct; degrading to "wrong key" is not.
"""

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import settings

# 96 bits, the value GCM is specified and optimised for. Longer nonces are
# rehashed internally and gain nothing.
NONCE_BYTES = 12
KEY_BYTES = 32  # AES-256


class CredentialEncryptionError(RuntimeError):
    """Encryption could not be performed — almost always misconfiguration."""


class CredentialDecryptionError(RuntimeError):
    """Ciphertext failed to authenticate: wrong key, wrong AAD, or tampering."""


def _load_key(raw: str | None, *, label: str) -> bytes | None:
    if raw is None:
        return None
    try:
        key = base64.b64decode(raw, validate=True)
    except Exception as exc:  # noqa: BLE001 - surfaced as configuration error
        raise CredentialEncryptionError(
            f"{label} is not valid base64. Generate one with: "
            'python -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"'
        ) from exc

    if len(key) != KEY_BYTES:
        raise CredentialEncryptionError(
            f"{label} must decode to exactly {KEY_BYTES} bytes (AES-256), got {len(key)}."
        )
    return key


def _current_key() -> bytes:
    key = _load_key(
        settings.credential_encryption_key.get_secret_value()
        if settings.credential_encryption_key
        else None,
        label="CREDENTIAL_ENCRYPTION_KEY",
    )
    if key is None:
        raise CredentialEncryptionError(
            "CREDENTIAL_ENCRYPTION_KEY is not set. BYOK credentials cannot be stored."
        )
    return key


def _key_for_version(version: int) -> bytes:
    """Resolve the key that encrypted a given row.

    During rotation both keys are configured; rows written before the rotation
    carry the older version and are decrypted with the previous key.
    """
    if version == settings.credential_key_version:
        return _current_key()

    previous = _load_key(
        settings.credential_encryption_key_previous.get_secret_value()
        if settings.credential_encryption_key_previous
        else None,
        label="CREDENTIAL_ENCRYPTION_KEY_PREVIOUS",
    )
    if previous is None:
        raise CredentialDecryptionError(
            f"Credential was encrypted with key version {version}, but only version "
            f"{settings.credential_key_version} is configured. Set "
            "CREDENTIAL_ENCRYPTION_KEY_PREVIOUS to decrypt it."
        )
    return previous


def build_aad(user_id: str, provider: str) -> bytes:
    """Bind a ciphertext to its owner and provider. See module docstring."""
    return f"{user_id}:{provider}".encode()


def encrypt_credential(plaintext: str, *, aad: bytes) -> tuple[bytes, bytes, int]:
    """Encrypt an API key.

    Returns `(ciphertext, nonce, key_version)` for direct storage on
    `UserLLMCredential`. A fresh random nonce per call — reusing a nonce under
    the same key is the one catastrophic misuse of GCM, as it leaks the
    authentication subkey.
    """
    if not plaintext:
        raise CredentialEncryptionError("Refusing to encrypt an empty credential.")

    key = _current_key()
    nonce = os.urandom(NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext.encode(), aad)
    return ciphertext, nonce, settings.credential_key_version


def decrypt_credential(ciphertext: bytes, nonce: bytes, key_version: int, *, aad: bytes) -> str:
    """Decrypt an API key. Raises rather than returning anything partial."""
    key = _key_for_version(key_version)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, aad).decode()
    except InvalidTag as exc:
        # Deliberately vague: the caller cannot distinguish a wrong key from
        # tampering, and neither should an error message reaching a log.
        raise CredentialDecryptionError(
            "Credential failed authentication. The encryption key may have changed, "
            "or the row may have been altered."
        ) from exc


def last_four(plaintext: str) -> str:
    """Display suffix, stored in plaintext so the settings UI never decrypts."""
    return plaintext[-4:] if len(plaintext) >= 4 else plaintext
