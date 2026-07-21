"""Credits and billing — **schema only, dormant**.

Nothing reads or writes these tables in Phase 1. They exist now because adding
billing tables later means a migration against a table with real rows, while
adding them today costs one empty migration (docs/DECISIONS.md D7).

The Phase 1 product is: BYOK free and unlimited, plus 5 lifetime platform
generations. That free grant is the only thing these tables will meter when they
do wake up — under D7 credits recover *our* inference cost; margin comes from
subscriptions, not from token markup.

Design note: `CreditTransaction` is an **append-only ledger**, and
`UserCreditBalance` is a cache of its sum. Ledgers are the standard shape for
anything money-adjacent because they are auditable and reconstructable — you can
always recompute the balance and find where it diverged. Never mutate a
transaction row; write a compensating one.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from ..db.session import Base
from .enums import CreditTransactionKind, SubscriptionStatus, enum_column
from .mixins import TimestampMixin


class UserCreditBalance(Base, TimestampMixin):
    """Cached sum of the ledger. Derived data — the ledger is the truth."""

    __tablename__ = "user_credit_balances"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    balance = Column(Integer, nullable=False, server_default=text("0"))
    lifetime_granted = Column(Integer, nullable=False, server_default=text("0"))
    lifetime_consumed = Column(Integer, nullable=False, server_default=text("0"))


class CreditTransaction(Base):
    """Append-only. One row per credit movement, positive or negative."""

    __tablename__ = "credit_transactions"

    __table_args__ = (
        Index("idx_credit_tx_user_created", "user_id", "created_at"),
        # Idempotency: a Stripe webhook can be delivered more than once, and a
        # retried generation must not double-charge. Writers set a stable key and
        # let the database reject the duplicate.
        UniqueConstraint("idempotency_key", name="uq_credit_tx_idempotency"),
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

    kind = Column(enum_column(CreditTransactionKind, "credit_transaction_kind"), nullable=False)

    # Signed: positive grants, negative consumption.
    amount = Column(Integer, nullable=False)
    # Balance after this row was applied, so history is readable without
    # replaying the whole ledger.
    balance_after = Column(Integer, nullable=False)

    description = Column(Text, nullable=True)
    # Loose pointer to whatever caused this (tutorial_instance id, Stripe event
    # id). Deliberately not an FK — the referent lives in different tables.
    reference_id = Column(String(255), nullable=True)
    idempotency_key = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )


class BillingCustomer(Base, TimestampMixin):
    """Maps a user to their Stripe customer. Separate from `users` so the auth
    path never loads billing data it doesn't need."""

    __tablename__ = "billing_customers"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    stripe_customer_id = Column(String(255), nullable=False, unique=True)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    __table_args__ = (Index("idx_subscription_user", "user_id"),)

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

    stripe_subscription_id = Column(String(255), nullable=False, unique=True)
    status = Column(enum_column(SubscriptionStatus, "subscription_status"), nullable=False)

    # Free-form rather than an enum: plan names change for marketing reasons far
    # more often than schemas should.
    plan = Column(String(100), nullable=False)

    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, server_default=text("false"))
