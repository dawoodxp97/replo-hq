"""cascade orchestration fks

Revision ID: a5b0a1b30fd5
Revises: d677502085c4
Create Date: 2026-07-23 09:12:28.028810

`tutorial_executions.tutorial_instance_id` and
`tutorial_step_executions.tutorial_execution_id` were created without an
`ON DELETE` action, so they defaulted to NO ACTION.

The ORM declares `cascade="all, delete-orphan"` on both relationships, which is
why this looked correct in the model. That cascade only applies when SQLAlchemy
traverses the relationship itself. Deleting a **user** cascades to
`tutorial_instances` in the database, which never loads the execution rows — so
Postgres aborted the transaction:

    ForeignKeyViolationError: update or delete on table "tutorial_instances"
    violates foreign key constraint
    "tutorial_executions_tutorial_instance_id_fkey"

`POST /api/settings/security/delete-account` therefore failed for any user who
had ever started a generation. Found when a test's own cleanup hit it.

Written by hand: alembic autogenerate does **not** detect a changed `ondelete`
rule — the same blind spot it has for CHECK constraints (see app/models/CLAUDE.md).
It compares FK columns, not their referential actions, so this migration comes out
empty if generated.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5b0a1b30fd5"
down_revision: str | Sequence[str] | None = "d677502085c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (table, constraint name, column, referenced table, referenced column)
_FOREIGN_KEYS = [
    (
        "tutorial_executions",
        "tutorial_executions_tutorial_instance_id_fkey",
        "tutorial_instance_id",
        "tutorial_instances",
        "id",
    ),
    (
        "tutorial_step_executions",
        "tutorial_step_executions_tutorial_execution_id_fkey",
        "tutorial_execution_id",
        "tutorial_executions",
        "id",
    ),
]


def upgrade() -> None:
    """A referential action cannot be altered in place — drop and recreate."""
    for table, name, column, ref_table, ref_column in _FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name,
            table,
            ref_table,
            [column],
            [ref_column],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    for table, name, column, ref_table, ref_column in _FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, ref_table, [column], [ref_column])
