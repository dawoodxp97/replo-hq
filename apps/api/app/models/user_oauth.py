"""OAuth provider identities (D10).

One row per (user, provider) link. A user may hold several identities — password
plus GitHub plus Google — and they are all the same account: every provider
mints the same JWT session, so the session module never has to know how a user
signed in.

Why a separate table rather than columns on `users`: providers are open-ended
(new ones are one row shape, not a migration each), one user can hold several
identities simultaneously, and provider user ids are only unique *per provider*
— a global unique column would collide across GitHub and Google.
"""

from sqlalchemy import Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from ..db.session import Base
from .mixins import TimestampMixin


class UserOAuthIdentity(Base, TimestampMixin):
    __tablename__ = "user_oauth_identities"

    __table_args__ = (
        # One identity per provider account. (provider, provider_user_id) is the
        # natural key the provider guarantees; a second row for the same GitHub
        # login can only be an account-takeover attempt or a bug.
        UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_subject"),
        Index("idx_oauth_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    # "github" / "google" — the slug used in the authorize/callback URLs. A plain
    # string, not an enum: adding a provider must not require a migration, and
    # the router validates the value before it reaches this column.
    provider = Column(String(32), nullable=False)

    # The subject id the provider reports (GitHub numeric id, Google `sub`).
    # Stable across email changes — which is why identity matching prefers it
    # over email.
    provider_user_id = Column(String(255), nullable=False)

    # Snapshot of the email the provider reported at link time. Informational:
    # the authoritative email lives on `users` and is re-read on each login.
    provider_email = Column(String(255), nullable=True)

    user = relationship("User", back_populates="oauth_identities")
