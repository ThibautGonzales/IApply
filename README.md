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
└── DECISIONS.md
```

## Getting started

Setup instructions will be added as the project grows.
