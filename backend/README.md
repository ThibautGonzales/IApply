# IApply backend

FastAPI application.

## Run locally (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Point to a running PostgreSQL (for example the one from docker compose)
export DATABASE_URL=postgresql+psycopg://iapply:iapply@localhost:5432/iapply
fastapi dev app/main.py        # http://localhost:8000/health and /docs
```

## Run the tests

Tests use an in-memory SQLite database (see `tests/conftest.py`), so they
don't need PostgreSQL.

```bash
cd backend
python -m pytest
```
