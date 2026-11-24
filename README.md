# IApply

IApply helps with job hunting: it collects job offers (from Jooble today), scores
them against your profile with an LLM (planned), and later drafts cover letters.

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
├── backend/    # FastAPI application (API, database, job sources, LLM calls)
├── frontend/   # Angular application (user interface)
├── docker-compose.yml  # Runs the database, backend and frontend together
└── DECISIONS.md
```

## Getting started

Requirements: Docker Desktop.

```bash
docker compose up --build
```

Then open:

- http://localhost:4200: the app, showing "Backend status: API ok, database ok"
- http://localhost:8000/health: the API directly, answering `{"status": "ok", "database": "ok"}`
- http://localhost:8000/docs: the API documentation

Settings live in `.env` (copy `.env.example` to `.env`): database credentials and
the job search (Jooble key, keywords, location, radius, remote offers). Without a
`.env`, the defaults from `docker-compose.yml` are used, but collecting offers
needs at least `JOOBLE_API_KEY`.

## Collecting job offers

1. Get a free Jooble API key from the French page, https://fr.jooble.org/api/about
   (a key only works on the host of its country), and put it in `.env` as
   `JOOBLE_API_KEY`.
2. Open http://localhost:4200 and click **Collect**. It fetches the offers published
   since the latest one already saved (7 days back the first time), saves the new
   ones and lists them, on-site and remote apart, each linking to the original posting.

The free key allows 100 calls a day; one collection uses about 6 to 10.

API routes: `POST /jobs/collect` runs a collection, `GET /jobs` lists the saved offers.

To run without Docker, see [backend/README.md](backend/README.md) and
[frontend/README.md](frontend/README.md).
