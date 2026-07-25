from sqlalchemy import Column, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from ..db.session import Base
from .enums import RepositoryStatus, enum_column
from .mixins import TimestampMixin


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"

    __table_args__ = (
        Index("idx_repo_user", "user_id"),
        # The tenancy fix. `github_url` used to carry a bare `unique=True`,
        # meaning the URL was unique across the *entire product*: once one user
        # added github.com/facebook/react, no other user ever could. Uniqueness
        # belongs per-owner.
        UniqueConstraint("user_id", "github_url", name="uq_repo_user_url"),
        # Trigram GIN index backing services/search.py. Declared here, not only in
        # the migration, or `alembic check` reads the DB index as drift and
        # autogenerate offers to drop it. See migration 80e2e03a0776 for why a
        # B-tree cannot serve `ILIKE '%…%'`.
        Index(
            "idx_trgm_repo_name",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    repo_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )

    github_url = Column(String(255), nullable=False)
    name = Column(String(255))
    description = Column(Text)

    status = Column(
        enum_column(RepositoryStatus, "repository_status"),
        nullable=False,
        server_default=RepositoryStatus.PENDING.value,
    )
