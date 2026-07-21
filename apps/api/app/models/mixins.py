"""Reusable column groups.

`users` had no `created_at` at all — there was no way to answer "when did this
person sign up", which is the first question any product analytics asks.
"""

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """`created_at` / `updated_at`, both database-driven.

    Server-side defaults rather than Python ones: the database clock is the
    single source of truth, and rows created by a migration or by raw SQL get
    correct timestamps without the application being involved.
    """

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
