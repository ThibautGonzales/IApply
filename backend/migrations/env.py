from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

import app.models  # noqa: F401  (registers the tables in SQLModel.metadata)
from app.database import engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic compares this metadata with the database to autogenerate migrations.
# Models must be imported (via app.models) so their tables are registered in it.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Generate the SQL script without connecting to the database (`alembic upgrade --sql`)."""
    context.configure(
        url=str(engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply the migrations on the database the app uses."""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
