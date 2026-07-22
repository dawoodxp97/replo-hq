from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from ..db.session import Base
from .mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    email = Column(String, unique=True, index=True, nullable=False)

    # Nullable: GitHub OAuth users (Phase 2.8) never set a password. A NOT NULL
    # column would force storing a dummy hash, which is indistinguishable from a
    # real one and therefore a login bypass waiting to happen.
    hashed_password = Column(String, nullable=True)

    # Lets an account be disabled without deleting it and cascading away every
    # tutorial they own.
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    # Tokens issued before this instant are rejected. Bumped on password change
    # and on "sign out everywhere".
    #
    # Without it a password change did nothing to existing sessions: refresh
    # tokens live 30 days, so an attacker holding one keeps access for a month
    # after the victim changes their password — which is precisely the action
    # taken *because* of a suspected compromise.
    #
    # This is a stopgap, not the real fix. Proper refresh-token rotation with
    # reuse detection needs a token store; a single timestamp can only revoke
    # everything at once, never one device.
    sessions_valid_from = Column(DateTime(timezone=True), nullable=True)

    # Add relationships later if needed, e.g.:
    # tutorials = relationship("Tutorial", back_populates="owner")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
