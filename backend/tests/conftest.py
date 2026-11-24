import os

# Tests use an in-memory SQLite database, so they run without PostgreSQL.
# This must be set before `app.database` is imported.
os.environ.setdefault("DATABASE_URL", "sqlite://")
