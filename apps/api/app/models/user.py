from sqlalchemy import Boolean, Column, String
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

    # Add relationships later if needed, e.g.:
    # tutorials = relationship("Tutorial", back_populates="owner")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
