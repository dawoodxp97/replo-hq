"""Alembic environment.

The database URL is NOT stored in alembic.ini. It comes from the same
pydantic-settings object the application uses, so migrations can never run
against a different database than the app — and no credentials sit in a
tracked file.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Importing the package registers every model on Base.metadata. Without this,
# autogenerate sees an empty schema and helpfully offers to drop all your tables.
import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.db.session import Base

config = context.config

# Injected at runtime rather than read from alembic.ini.
#
# The `%` doubling is required, not cosmetic: alembic stores this in a
# configparser, which treats `%` as interpolation syntax. A password containing
# a character that URL-encodes to a percent escape (`@` -> `%40`, ` ` -> `%20`)
# otherwise raises "invalid interpolation syntax" and no migration can run.
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting. Useful for reviewing a migration."""
    context.configure(
        url=settings.sqlalchemy_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Without these two, autogenerate silently misses column type and
            # default changes — which is how schemas drift from models.
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
