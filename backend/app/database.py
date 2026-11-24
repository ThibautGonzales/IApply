import os

from sqlalchemy import text
from sqlmodel import Session, create_engine

# Read from the environment so the same code works in Docker, locally and in tests.
DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)


def is_database_reachable() -> bool:
    """Run a trivial query to check that the database answers."""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_session():
    """FastAPI dependency: one database session per request, closed afterwards."""
    with Session(engine) as session:
        yield session
