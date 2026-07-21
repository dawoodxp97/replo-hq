"""Domain enums.

Replaces bare strings scattered across models, where `Repository.status` used
`'PENDING'` while the orchestration tables used `'pending'` for the same concept,
and nothing at any layer rejected a typo.

**All values are lowercase.** The uppercase variants are migrated in place.

Two deliberate choices:

1. `StrEnum` (not bare `Enum`) so a member compares equal to its string value.
   Existing comparisons like `repo.status == "completed"` keep working, and
   FastAPI/pydantic serialise them as plain strings without a custom encoder.
   `str(member)` also yields the value rather than `"RepositoryStatus.PENDING"`,
   which is what makes them safe to drop straight into log lines and f-strings.

2. Columns use `native_enum=False`, producing `VARCHAR + CHECK` instead of a
   Postgres `ENUM` type. Native enums cannot drop a value, and
   `ALTER TYPE ... ADD VALUE` cannot run inside a transaction — which means every
   future status change would be an out-of-band migration. A CHECK constraint is
   rewritten in a normal transactional migration.
"""

from enum import Enum, StrEnum

from sqlalchemy import Enum as SAEnum


class RepositoryStatus(StrEnum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunStatus(StrEnum):
    """Shared by TutorialInstance, TutorialExecution and TutorialStepExecution.

    One vocabulary for one concept — the three tables previously each declared
    their own overlapping-but-not-identical set of strings.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TutorialLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionType(StrEnum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


class NotificationType(StrEnum):
    DEFAULT = "default"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"


class LLMProvider(StrEnum):
    """Where a user's BYOK credential points.

    CUSTOM covers any OpenAI-compatible endpoint (local Ollama, LiteLLM proxy, a
    self-hosted gateway) — which is why `user_llm_credentials.base_url` exists.
    """

    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class CreditTransactionKind(StrEnum):
    """Append-only ledger entry types. Dormant until Phase 2 monetisation."""

    SIGNUP_GRANT = "signup_grant"
    GENERATION = "generation"
    PURCHASE = "purchase"
    SUBSCRIPTION_GRANT = "subscription_grant"
    REFUND = "refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class SubscriptionStatus(StrEnum):
    """Mirrors Stripe's subscription statuses so webhook payloads map directly."""

    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"
    PAUSED = "paused"


class TutorialVisibility(StrEnum):
    """Public tutorials are the growth channel (see docs/DECISIONS.md D8).

    Present from the first Phase 2 migration rather than retrofitted, because
    adding it later would mean touching the auth model, the router, the schema
    and apps/site simultaneously.
    """

    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"


def enum_column(enum_cls: type[Enum], name: str) -> SAEnum:
    """Build a VARCHAR+CHECK column type storing enum *values*, not names.

    Without `values_callable`, SQLAlchemy persists `member.name` — so
    `TutorialLevel.BEGINNER` would be stored as `'BEGINNER'`, reintroducing the
    exact casing inconsistency this module exists to remove.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )
