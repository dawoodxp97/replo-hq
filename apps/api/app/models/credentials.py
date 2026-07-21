"""BYOK credential storage.

Holds keys that bill **the user's** account, which makes this the highest-risk
table in the product. Design constraints, from docs/DECISIONS.md D9:

- The plaintext key exists only inside `app/core/crypto.py` and the outbound HTTP
  request. It is never returned by any API, never logged, and never placed in
  step context — see the warning below.
- `key_version` exists from day one so rotating the KEK, or moving to full KMS
  envelope encryption, is a migration rather than a rewrite.
- The plaintext display fields (`provider`, `label`, `last_four`) exist so the
  settings UI can render the list **without decrypting anything**.

⚠️  The credential must never enter the orchestrator's step context.
`TutorialStepExecution.input_data` and `output_data` persist the whole
accumulating context dict to Postgres verbatim. Steps receive `user_id`; the AI
client resolves the credential at call time and does not return it. That is a
structural guarantee, not a convention to remember.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from ..db.session import Base
from .enums import LLMProvider, enum_column
from .mixins import TimestampMixin


class UserLLMCredential(Base, TimestampMixin):
    __tablename__ = "user_llm_credentials"

    __table_args__ = (
        Index("idx_credential_user", "user_id"),
        # One label per provider per user, so the settings list is unambiguous.
        UniqueConstraint("user_id", "provider", "label", name="uq_credential_user_provider_label"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    provider = Column(
        enum_column(LLMProvider, "llm_provider"),
        nullable=False,
        server_default=LLMProvider.OPENROUTER.value,
    )

    # User-facing name, e.g. "work key". Not secret.
    label = Column(String(100), nullable=False, server_default="default")

    # --- Encrypted material -------------------------------------------------
    # AES-256-GCM. LargeBinary (bytea) rather than text: no base64 round-trip,
    # and it makes accidental logging produce obvious binary garbage rather than
    # a plausible-looking string someone might paste somewhere.
    ciphertext = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False)
    key_version = Column(Integer, nullable=False, server_default=text("1"))

    # --- Plaintext display fields -------------------------------------------
    # Rendering the settings page must never require decryption.
    last_four = Column(String(4), nullable=False)

    # Custom endpoint for OpenAI-compatible providers (Ollama, LiteLLM, gateways).
    base_url = Column(String(500), nullable=True)
    # Preferred model for this credential; falls back to the platform default.
    default_model = Column(String(200), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    # Set when the key last passed a live check. A key can be revoked upstream at
    # any time, so this is a hint for the UI, never an authorisation decision.
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
