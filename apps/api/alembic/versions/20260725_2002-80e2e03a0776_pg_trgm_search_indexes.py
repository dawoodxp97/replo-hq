"""pg_trgm search indexes

Revision ID: 80e2e03a0776
Revises: a5b0a1b30fd5
Create Date: 2026-07-25 20:02:35.070660

`search.py` filters every entity with `ILIKE '%term%'`. A leading wildcard makes
a B-tree useless, so each of those was a sequential scan — of `modules`, whose
`content_markdown` column is the largest in the schema.

`pg_trgm` GIN indexes are the fix that fits an `ILIKE '%…%'` pattern (a plain
full-text `tsvector` would not — it matches lexemes, not substrings, so it could
not find "uth" inside "authentication"). Trigram indexes are consulted only when
the pattern has at least 3 non-wildcard characters; shorter queries still scan,
which is why the service caps the result set regardless.

Written by hand: alembic does not autogenerate `CREATE EXTENSION`, and it renders
a GIN/opclass index as a plain `create_index` that drops the `gin_trgm_ops`
operator class, silently producing an index the planner cannot use for ILIKE.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "80e2e03a0776"
down_revision: str | Sequence[str] | None = "a5b0a1b30fd5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (index name, table, column)
_TRIGRAM_INDEXES = [
    ("idx_trgm_repo_name", "repositories", "name"),
    ("idx_trgm_tutorial_title", "tutorials", "title"),
    ("idx_trgm_module_title", "modules", "title"),
    # The one that mattered most: substring search over full module bodies.
    ("idx_trgm_module_content", "modules", "content_markdown"),
    ("idx_trgm_quiz_question", "quizzes", "question_text"),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    for name, table, column in _TRIGRAM_INDEXES:
        # Plain CREATE INDEX, not CONCURRENTLY: the app is not yet deployed and
        # has no data, so the table lock is instantaneous. A production run
        # against a populated table should switch to CONCURRENTLY — which cannot
        # run inside alembic's transaction and needs its own migration with
        # `op.get_context().autocommit_block()`.
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {name} "
            f"ON {table} USING gin ({column} gin_trgm_ops)"
        )


def downgrade() -> None:
    for name, _table, _column in _TRIGRAM_INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    # The extension is left installed: other things may come to depend on it, and
    # dropping it would fail if any index still referenced it.
