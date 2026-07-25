from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from ..db.session import Base
from .enums import TutorialLevel, TutorialVisibility, enum_column


class Tutorial(Base):
    __tablename__ = "tutorials"

    __table_args__ = (
        Index("idx_tutorial_repo", "repo_id"),
        # Serves /explore and the sitemap: "public tutorials, newest first".
        # Partial index — private rows are the majority and are never in this
        # query, so excluding them keeps the index small.
        Index(
            "idx_tutorial_public_published",
            "published_at",
            postgresql_where=text("visibility = 'public'"),
        ),
        # Trigram GIN index for services/search.py (see migration 80e2e03a0776).
        Index(
            "idx_trgm_tutorial_title",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    tutorial_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    repo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("repositories.repo_id", ondelete="CASCADE"),
        nullable=False,
    )

    level = Column(
        enum_column(TutorialLevel, "tutorial_level"),
        nullable=False,
        server_default=TutorialLevel.INTERMEDIATE.value,
    )

    title = Column(String(255), nullable=False)
    overview = Column(Text)
    overview_diagram_mermaid = Column(Text)  # For the main dependency graph

    # --- Public surface (docs/DECISIONS.md D8) ------------------------------
    #
    # Present from the first Phase 2 migration rather than retrofitted: adding a
    # public surface later means touching the auth model (anonymous reads), the
    # router, the schema (backfilled across existing rows) and apps/site at once.
    #
    # PRIVATE by default. Publishing is an explicit act, never a side effect of
    # generation.
    visibility = Column(
        enum_column(TutorialVisibility, "tutorial_visibility"),
        nullable=False,
        server_default=TutorialVisibility.PRIVATE.value,
    )

    # Globally unique — it addresses /t/{slug} on apps/site, so uniqueness cannot
    # be per-user. Collisions are resolved at generation time by appending a
    # short suffix.
    slug = Column(String(280), nullable=True, unique=True)

    # Distinct from generated_at: a tutorial can be generated today and published
    # next week. Also what /explore and the sitemap order by.
    published_at = Column(DateTime(timezone=True), nullable=True)

    # `generated_at` is domain-meaningful (when the pipeline produced this), so it
    # stays rather than being folded into TimestampMixin's created_at. `updated_at`
    # is added separately so authoring edits are distinguishable from generation.
    generated_at = Column(
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
