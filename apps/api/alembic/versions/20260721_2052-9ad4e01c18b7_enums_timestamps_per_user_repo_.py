"""enums, timestamps, per-user repo uniqueness

Revision ID: 9ad4e01c18b7
Revises: 7b1291fb0c9b
Create Date: 2026-07-21 20:52:29.348217

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ad4e01c18b7"
down_revision: str | Sequence[str] | None = "7b1291fb0c9b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # --- Data migration, BEFORE any type change -----------------------------
    #
    # Status values were inconsistently cased: `repositories.status` stored
    # 'PENDING'/'COMPLETED' while the orchestration tables used lowercase for the
    # same concept. Everything is lowercase from here on.
    #
    # This must run first. The new columns carry CHECK constraints accepting only
    # lowercase values, so an existing 'COMPLETED' row would fail the constraint
    # and abort the migration.
    op.execute("UPDATE repositories SET status = lower(status)")
    op.execute("UPDATE tutorials SET level = lower(level)")
    op.execute("UPDATE quizzes SET question_type = lower(question_type)")
    op.execute("UPDATE notifications SET type = lower(type)")
    op.execute(
        "UPDATE user_settings SET default_difficulty_level = lower(default_difficulty_level)"
    )
    op.execute("UPDATE tutorial_instances SET status = lower(status)")
    op.execute("UPDATE tutorial_executions SET status = lower(status)")
    op.execute("UPDATE tutorial_step_executions SET status = lower(status)")

    # Columns becoming NOT NULL: backfill anything the ORM-side `default=` never
    # covered (rows written by raw SQL, or by the drop_all/create_all script).
    op.execute("UPDATE tutorial_instances SET status = 'pending' WHERE status IS NULL")
    op.execute("UPDATE tutorial_instances SET created_at = now() WHERE created_at IS NULL")
    op.execute("UPDATE tutorial_instances SET updated_at = now() WHERE updated_at IS NULL")
    op.execute("UPDATE tutorial_executions SET status = 'pending' WHERE status IS NULL")
    op.execute(
        "UPDATE tutorial_executions SET current_step_order = 0 WHERE current_step_order IS NULL"
    )
    op.execute("UPDATE tutorial_step_executions SET status = 'pending' WHERE status IS NULL")
    op.execute(
        "UPDATE user_settings SET default_difficulty_level = 'beginner' "
        "WHERE default_difficulty_level IS NULL"
    )

    # --- Schema ------------------------------------------------------------
    op.add_column(
        "modules",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "modules",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.Enum(
            "default", "info", "success", "warning", name="notification_type", native_enum=False
        ),
        existing_nullable=False,
        existing_server_default=sa.text("'default'::character varying"),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "quizzes",
        "question_type",
        existing_type=sa.VARCHAR(length=50),
        server_default="multiple_choice",
        type_=sa.Enum("multiple_choice", "true_false", name="question_type", native_enum=False),
        existing_nullable=False,
    )
    op.alter_column(
        "repositories",
        "status",
        existing_type=sa.VARCHAR(length=50),
        server_default="pending",
        type_=sa.Enum(
            "pending",
            "analyzing",
            "completed",
            "failed",
            name="repository_status",
            native_enum=False,
        ),
        existing_nullable=False,
    )
    op.drop_constraint(op.f("repositories_github_url_key"), "repositories", type_="unique")
    op.create_unique_constraint("uq_repo_user_url", "repositories", ["user_id", "github_url"])
    op.add_column("tutorial_executions", sa.Column("error_message", sa.Text(), nullable=True))
    op.alter_column(
        "tutorial_executions",
        "status",
        existing_type=sa.VARCHAR(),
        server_default="pending",
        nullable=False,
    )
    op.alter_column(
        "tutorial_executions",
        "current_step_order",
        existing_type=sa.INTEGER(),
        server_default=sa.text("0"),
        nullable=False,
    )
    op.alter_column(
        "tutorial_instances",
        "status",
        existing_type=sa.VARCHAR(),
        server_default="pending",
        nullable=False,
    )
    op.alter_column(
        "tutorial_instances",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "tutorial_instances",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.drop_constraint(
        op.f("tutorial_instances_user_id_fkey"), "tutorial_instances", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "tutorial_instances", "users", ["user_id"], ["user_id"], ondelete="CASCADE"
    )
    op.alter_column(
        "tutorial_step_executions",
        "status",
        existing_type=sa.VARCHAR(),
        server_default="pending",
        nullable=False,
    )
    op.add_column(
        "tutorials",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "tutorials",
        "level",
        existing_type=sa.VARCHAR(length=50),
        server_default="intermediate",
        type_=sa.Enum(
            "beginner", "intermediate", "advanced", name="tutorial_level", native_enum=False
        ),
        existing_nullable=False,
    )
    op.add_column(
        "user_settings",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "user_settings",
        "default_difficulty_level",
        existing_type=sa.VARCHAR(),
        server_default="beginner",
        nullable=False,
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###

    # --- CHECK constraints -------------------------------------------------
    #
    # Written by hand because **Alembic does not autogenerate CHECK
    # constraints**. `alter_column(type_=sa.Enum(..., native_enum=False))` widens
    # the VARCHAR and stops there. Verified on a scratch database: without this
    # block the schema has zero CHECK constraints and Postgres accepts any string
    # in a status column — the enums would be Python-side decoration only.
    #
    # Values are frozen literals, not references to app.models.enums. A migration
    # describes one historical transition; if it imported the live enum it would
    # silently change meaning every time someone edits the model.
    for table, column, constraint, allowed in [
        (
            "repositories",
            "status",
            "ck_repositories_status",
            ("pending", "analyzing", "completed", "failed"),
        ),
        ("tutorials", "level", "ck_tutorials_level", ("beginner", "intermediate", "advanced")),
        ("quizzes", "question_type", "ck_quizzes_question_type", ("multiple_choice", "true_false")),
        (
            "notifications",
            "type",
            "ck_notifications_type",
            ("default", "info", "success", "warning"),
        ),
        (
            "user_settings",
            "default_difficulty_level",
            "ck_user_settings_difficulty",
            ("beginner", "intermediate", "advanced"),
        ),
        (
            "tutorial_instances",
            "status",
            "ck_tutorial_instances_status",
            ("pending", "running", "completed", "failed"),
        ),
        (
            "tutorial_executions",
            "status",
            "ck_tutorial_executions_status",
            ("pending", "running", "completed", "failed"),
        ),
        (
            "tutorial_step_executions",
            "status",
            "ck_tutorial_step_executions_status",
            ("pending", "running", "completed", "failed"),
        ),
    ]:
        values = ", ".join(f"'{v}'" for v in allowed)
        op.create_check_constraint(constraint, table, f"{column} IN ({values})")


def downgrade() -> None:
    """Downgrade schema."""
    for table, constraint in [
        ("repositories", "ck_repositories_status"),
        ("tutorials", "ck_tutorials_level"),
        ("quizzes", "ck_quizzes_question_type"),
        ("notifications", "ck_notifications_type"),
        ("user_settings", "ck_user_settings_difficulty"),
        ("tutorial_instances", "ck_tutorial_instances_status"),
        ("tutorial_executions", "ck_tutorial_executions_status"),
        ("tutorial_step_executions", "ck_tutorial_step_executions_status"),
    ]:
        op.drop_constraint(constraint, table, type_="check")

    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
    op.drop_column("users", "is_active")
    op.alter_column(
        "user_settings",
        "default_difficulty_level",
        existing_type=sa.VARCHAR(),
        server_default=None,
        nullable=True,
    )
    op.drop_column("user_settings", "updated_at")
    op.drop_column("user_settings", "created_at")
    op.alter_column(
        "tutorials",
        "level",
        existing_type=sa.Enum(
            "beginner", "intermediate", "advanced", name="tutorial_level", native_enum=False
        ),
        server_default=None,
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.drop_column("tutorials", "updated_at")
    op.alter_column(
        "tutorial_step_executions",
        "status",
        existing_type=sa.VARCHAR(),
        server_default=None,
        nullable=True,
    )
    op.drop_constraint(None, "tutorial_instances", type_="foreignkey")
    op.create_foreign_key(
        op.f("tutorial_instances_user_id_fkey"),
        "tutorial_instances",
        "users",
        ["user_id"],
        ["user_id"],
    )
    op.alter_column(
        "tutorial_instances",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "tutorial_instances",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "tutorial_instances",
        "status",
        existing_type=sa.VARCHAR(),
        server_default=None,
        nullable=True,
    )
    op.alter_column(
        "tutorial_executions",
        "current_step_order",
        existing_type=sa.INTEGER(),
        server_default=None,
        nullable=True,
    )
    op.alter_column(
        "tutorial_executions",
        "status",
        existing_type=sa.VARCHAR(),
        server_default=None,
        nullable=True,
    )
    op.drop_column("tutorial_executions", "error_message")
    op.drop_constraint("uq_repo_user_url", "repositories", type_="unique")
    op.create_unique_constraint(
        op.f("repositories_github_url_key"),
        "repositories",
        ["github_url"],
        postgresql_nulls_not_distinct=False,
    )
    op.alter_column(
        "repositories",
        "status",
        existing_type=sa.Enum(
            "pending",
            "analyzing",
            "completed",
            "failed",
            name="repository_status",
            native_enum=False,
        ),
        server_default=sa.text("'PENDING'::character varying"),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        "quizzes",
        "question_type",
        existing_type=sa.Enum(
            "multiple_choice", "true_false", name="question_type", native_enum=False
        ),
        server_default=sa.text("'MULTIPLE_CHOICE'::character varying"),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
    op.drop_column("quizzes", "updated_at")
    op.drop_column("quizzes", "created_at")
    op.alter_column(
        "notifications",
        "type",
        existing_type=sa.Enum(
            "default", "info", "success", "warning", name="notification_type", native_enum=False
        ),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
        existing_server_default=sa.text("'default'::character varying"),
    )
    op.drop_column("modules", "updated_at")
    op.drop_column("modules", "created_at")
    # ### end Alembic commands ###
