# IApply

IApply helps with job hunting: it collects job offers from the France Travail API,
scores them against your profile with an LLM, and (later) drafts cover letters.

## Stack

| Part | Technology |
|---|---|
| Backend | Python, FastAPI, SQLModel, Alembic, LangChain |
| Frontend | Angular |
| Database | PostgreSQL |
| Runtime | Docker Compose (frontend, backend, db) |

See [DECISIONS.md](DECISIONS.md) for why each choice was made.

## Project layout

```
IApply/
├── backend/    # FastAPI application (API, database, LLM calls)
├── frontend/   # Angular application (user interface)
├── docker-compose.yml  # Runs the database and the backend together
└── DECISIONS.md
```

## Getting started

Requirements: Docker Desktop.

```bash
docker compose up --build
```

Then open http://localhost:8000/health: it should answer
`{"status": "ok", "database": "ok"}`.

Default database credentials are set in `docker-compose.yml`. To change them,
copy `.env.example` to `.env` and edit it.

To run the backend without Docker, see [backend/README.md](backend/README.md).
