import os

import pytest

# Tests use an in-memory SQLite database, so they run without PostgreSQL.
# This must be set before `app.database` is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.database import engine  # noqa: E402

ALEMBIC_CONFIG = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))


@pytest.fixture
def session():
    """A session on a database built by our real migrations, emptied after each test."""
    command.upgrade(ALEMBIC_CONFIG, "head")
    with Session(engine) as session:
        yield session
    command.downgrade(ALEMBIC_CONFIG, "base")
