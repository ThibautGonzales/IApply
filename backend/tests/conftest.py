import os

import pytest

# Tests use an in-memory SQLite database, so they run without PostgreSQL.
# This must be set before `app.database` is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")

from alembic import command  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, create_engine  # noqa: E402

from app import database  # noqa: E402
from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402

# One shared connection for the whole test run: an in-memory SQLite database
# lives inside its connection, and FastAPI's TestClient runs routes in another thread.
database.engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

ALEMBIC_CONFIG = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))


@pytest.fixture
def session():
    """A session on a database built by our real migrations, emptied after each test."""
    command.upgrade(ALEMBIC_CONFIG, "head")
    with Session(database.engine) as session:
        yield session
    command.downgrade(ALEMBIC_CONFIG, "base")


@pytest.fixture
def client(session):
    """API client whose routes use the test database."""
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
