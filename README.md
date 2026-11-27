# IApply

IApply helps with job hunting: it collects job offers from the Jooble API, lets you
add offers found elsewhere by pasting them, and (planned) scores them against your
profile with an LLM, drafts cover letters and tracks your applications.
See the roadmap in [DECISIONS.md](DECISIONS.md#2026-11-25--roadmap-update).

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
the Jooble key and host. Without a
`.env`, the defaults from `docker-compose.yml` are used, but collecting offers
needs at least `JOOBLE_API_KEY`.

## Collecting job offers

1. Get a free Jooble API key from the French page, https://fr.jooble.org/api/about
   (a key only works on the host of its country), and put it in `.env` as
   `JOOBLE_API_KEY`.
2. Choose an LLM on the **LLM** page, then describe what you are looking for on the
   **Profile** page and save: the LLM works out the Jooble searches from it.
3. Open http://localhost:4200 and click **Collect**. It fetches the offers published
   since the latest one already saved (7 days back the first time), saves the new
   ones and lists them, on-site and remote apart, each linking to the original posting.

The free key allows 100 calls a day; one collection uses about 6 to 10.

API routes: `POST /jobs/collect` runs a collection, `GET /jobs` lists the saved offers.

## Your profile

The **Profile** page holds what you are looking for, as plain text (job, technologies,
location, remote, contract, what to avoid). The LLM scores the offers against it and, when
you save a new text, works out from it the Jooble searches of the collection (at most 6,
each one a few keywords around a place, or full remote). They are listed under the text.
If the LLM fails, nothing is saved and the page shows why.

API routes: `GET /profile` reads it, `PUT /profile` saves it, `GET /profile/searches` lists the
Jooble searches.

To run without Docker, see [backend/README.md](backend/README.md) and
[frontend/README.md](frontend/README.md).
