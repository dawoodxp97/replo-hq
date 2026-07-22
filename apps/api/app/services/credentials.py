"""BYOK credential service.

**This module is the only decryption path in the application.** Everything else
— routers, the orchestrator, steps — works with `user_id` and never sees key
material.

That is what keeps plaintext out of `TutorialStepExecution.input_data`. The
orchestrator merges every step's output into one accumulating dict and persists
it verbatim to Postgres, so anything that enters step context is written to the
database in the clear, permanently, in a table nobody reads. The credential
cannot leak that way because it is never placed in the dict: steps carry
`user_id`, and `resolve_credential` is called at the moment of the LLM request.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.crypto import (
    CredentialDecryptionError,
    build_aad,
    decrypt_credential,
    encrypt_credential,
    last_four,
)
from ..core.net import validate_outbound_url
from ..models.credentials import UserLLMCredential
from ..models.enums import LLMProvider

logger = logging.getLogger(__name__)

# Where to send a validation request when the user hasn't supplied a base_url.
_DEFAULT_BASE_URLS: dict[LLMProvider, str] = {
    LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
    LLMProvider.OPENAI: "https://api.openai.com/v1",
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
}


@dataclass(frozen=True)
class ResolvedCredential:
    """Everything needed to make one LLM call.

    Deliberately **not** an ORM object: it is a short-lived value that exists for
    the duration of a request and is never attached to a session, so it cannot be
    accidentally persisted or lazily re-loaded somewhere else.
    """

    api_key: str
    provider: LLMProvider
    base_url: str
    default_model: str | None

    def __repr__(self) -> str:  # pragma: no cover - defensive
        # Never let an api_key reach a traceback, an f-string, or a log line via
        # the default dataclass repr, which would print every field.
        return (
            f"ResolvedCredential(provider={self.provider!r}, "
            f"base_url={self.base_url!r}, default_model={self.default_model!r}, "
            "api_key=***REDACTED***)"
        )


async def list_credentials(db: AsyncSession, user_id: UUID) -> list[UserLLMCredential]:
    """List a user's credentials. Decrypts nothing — the settings UI renders
    `provider`, `label` and `last_four`, all of which are stored in plaintext."""
    result = await db.execute(
        select(UserLLMCredential)
        .where(UserLLMCredential.user_id == user_id)
        .order_by(UserLLMCredential.created_at.desc())
    )
    return list(result.scalars().all())


async def store_credential(
    db: AsyncSession,
    *,
    user_id: UUID,
    provider: LLMProvider,
    api_key: str,
    label: str = "default",
    base_url: str | None = None,
    default_model: str | None = None,
) -> UserLLMCredential:
    """Encrypt and persist a credential, replacing any existing one with the
    same (user, provider, label).

    Replacing rather than erroring is deliberate: "paste a new key" is the
    action a user takes when rotating, and making them delete the old one first
    is friction with no security benefit.
    """
    api_key = api_key.strip()

    # Validated here as well as at the schema, because this function is callable
    # from anywhere and the stored value is what later gets fetched.
    if base_url:
        base_url = validate_outbound_url(base_url)

    aad = build_aad(str(user_id), provider.value)
    ciphertext, nonce, key_version = encrypt_credential(api_key, aad=aad)

    existing = (
        await db.execute(
            select(UserLLMCredential).where(
                UserLLMCredential.user_id == user_id,
                UserLLMCredential.provider == provider,
                UserLLMCredential.label == label,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.ciphertext = ciphertext
        existing.nonce = nonce
        existing.key_version = key_version
        existing.last_four = last_four(api_key)
        existing.base_url = base_url
        existing.default_model = default_model
        existing.is_active = True
        credential = existing
    else:
        credential = UserLLMCredential(
            user_id=user_id,
            provider=provider,
            label=label,
            ciphertext=ciphertext,
            nonce=nonce,
            key_version=key_version,
            last_four=last_four(api_key),
            base_url=base_url,
            default_model=default_model,
        )
        db.add(credential)

    await db.commit()
    await db.refresh(credential)
    return credential


async def mark_validated(db: AsyncSession, credential: UserLLMCredential) -> None:
    """Record that a key passed a live check.

    A UI hint only. The key can be revoked upstream a second later, so this is
    never consulted for an authorisation decision.
    """
    credential.last_validated_at = datetime.now(UTC)
    await db.commit()


async def resolve_credential(
    db: AsyncSession,
    user_id: UUID,
    provider: LLMProvider | None = None,
) -> ResolvedCredential | None:
    """Decrypt the active credential for a user. **The only decryption path.**

    Returns `None` when the user has no usable credential — including when
    decryption fails. A credential that cannot be decrypted is treated as
    absent, so the caller falls back to the platform key or reports "no key
    configured" rather than attempting a request with garbage.
    """
    stmt = select(UserLLMCredential).where(
        UserLLMCredential.user_id == user_id,
        UserLLMCredential.is_active.is_(True),
    )
    if provider is not None:
        stmt = stmt.where(UserLLMCredential.provider == provider)

    credential = (
        await db.execute(stmt.order_by(UserLLMCredential.created_at.desc()).limit(1))
    ).scalar_one_or_none()

    if credential is None:
        return None

    try:
        api_key = decrypt_credential(
            credential.ciphertext,
            credential.nonce,
            credential.key_version,
            aad=build_aad(str(credential.user_id), credential.provider.value),
        )
    except CredentialDecryptionError:
        # No key material in the log — the exception message is deliberately
        # non-specific and this call site adds only identifiers.
        logger.error(
            "Failed to decrypt credential %s for user %s (key_version=%s)",
            credential.id,
            user_id,
            credential.key_version,
        )
        return None

    base_url = credential.base_url or _DEFAULT_BASE_URLS.get(
        credential.provider, _DEFAULT_BASE_URLS[LLMProvider.OPENROUTER]
    )

    return ResolvedCredential(
        api_key=api_key,
        provider=credential.provider,
        base_url=base_url,
        default_model=credential.default_model,
    )


async def delete_credential(db: AsyncSession, user_id: UUID, credential_id: UUID) -> bool:
    """Delete a credential. Scoped by user_id so an id from another account
    cannot be deleted by guessing it."""
    credential = (
        await db.execute(
            select(UserLLMCredential).where(
                UserLLMCredential.id == credential_id,
                UserLLMCredential.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if credential is None:
        return False

    await db.delete(credential)
    await db.commit()
    return True


async def validate_credential(
    api_key: str,
    provider: LLMProvider,
    base_url: str | None = None,
    timeout_seconds: float = 10.0,
) -> tuple[bool, str | None]:
    """Check a key against the provider before storing it.

    Returns `(ok, error_message)`. Rejecting a bad key at paste time is far
    better than discovering it three minutes into a generation, when the user
    has already left the page.

    Deliberately cheap — a models/list call, not a completion, so validating
    costs the user nothing.
    """
    url_base = base_url or _DEFAULT_BASE_URLS.get(provider)
    if not url_base:
        return False, "No base URL configured for this provider."

    if provider is LLMProvider.ANTHROPIC:
        url = f"{url_base.rstrip('/')}/models"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    else:
        url = f"{url_base.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {api_key}"}

    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            # allow_redirects=False is load-bearing, not tidiness: without it a
            # perfectly public host can 302 to http://169.254.169.254/ and the
            # client follows it, defeating the address check in core/net.py
            # without needing DNS rebinding at all.
            session.get(url, headers=headers, allow_redirects=False) as response,
        ):
            if response.status == 200:
                return True, None
            if response.status in (401, 403):
                return False, "The provider rejected this key."
            return False, f"Provider returned HTTP {response.status}."
    except TimeoutError:
        return False, "Timed out contacting the provider."
    except aiohttp.ClientError as exc:
        # type name only — a ClientError's str() can contain the request URL,
        # and a custom base_url may carry a token in its query string.
        return False, f"Could not reach the provider ({type(exc).__name__})."
