# Decisions

Architecture decisions and the reason behind each one.

## 2026-11-24 — Initial stack

- **Backend: Python + FastAPI.** Python has the best LLM tooling; FastAPI is light,
  typed, and generates API docs automatically.
- **ORM: SQLModel + Alembic.** SQLModel shares one class between the database model
  and the API schema (less duplication). Alembic handles schema migrations.
- **LLM: LangChain.** One interface for several providers. Claude first; Gemini,
  OpenAI and Mistral can be added later without rewriting the scoring code.
- **Frontend: Angular.** Structured framework with clear conventions (components,
  services), which keeps the code easy to navigate.
- **Database: PostgreSQL.** Reliable, standard, and well supported by SQLModel.
- **Runtime: Docker Compose.** Frontend, backend and database start with a single
  command, with the same setup on every machine.

## MVP scope (planned, not built yet)

1. A "Collect" button fetches offers from the job sources (Jooble first), only those
   published since the last collection (about once a day). Done, see below.
2. The user's profile is pasted as plain text.
3. An LLM scores each offer against the profile; offers under a threshold are hidden.
4. Ranked list of offers with a direct link to each one.
5. Later: cover letter generation in the style of the user's existing letters.

## 2026-11-24 — Frontend to backend calls

- **The frontend calls `/api/...` on its own origin.** In Docker, nginx forwards
  `/api/` to the backend; with `ng serve`, `proxy.conf.json` does the same. The
  browser only ever talks to one origin, so no CORS setup is needed.

## 2026-11-24 — Job collection

- **Source: Jooble, not France Travail.** The France Travail "Offres d'emploi" API left
  the francetravail.io catalogue in October 2026 (access on request only). Adzuna was
  considered but its free tier is limited to test calls (£12/month after). Jooble is free
  (100 calls/day) and aggregates many French job boards. Adzuna or France Travail can be
  added later as extra sources.
- **Sources are plain modules exposing `fetch_jobs(since) -> list[JobOffer]`**, registered
  in `app/sources/__init__.py` (`SOURCES`). Simpler than an abstract class while there is
  one source.
- **"Since the last collection" = day of the most recent saved offer** of that source
  (7 days back the first time). No extra table; offers fetched twice are skipped thanks to
  the unique (`source`, `external_id`) constraint and a check before saving.
- **Jooble's date filter is not trusted**: it can return months-old offers, so older offers
  are dropped in our code.
- **Search settings are environment variables** (`JOOBLE_*` in `.env`) until a settings
  screen exists. Remote offers are a second search per keyword with the location
  "Télétravail" (`JOOBLE_INCLUDE_REMOTE`), and stored with `remote = true`.
- **Migrations run at backend startup** (`alembic upgrade head` in the Dockerfile), and
  tests build their database with the same migrations.
- **UI texts stay in English** for now; French/English switching (i18n) is a separate feature.

## 2026-11-24 — Interface languages (English / French)

- **A small `I18nService` with TypeScript dictionaries** (`frontend/src/app/core/i18n/`),
  the same system as MorningDevNews. The language switches at runtime with the EN / FR
  buttons, without reloading, and the choice is saved in `localStorage`.
- **Not `@angular/localize`**: it builds one site per language, so switching would reload
  another site; no extra dependency either.
- **English is the reference list of keys**: TypeScript reports any key missing in French.
- **Components keep raw data** (collection result, API health) and build texts in the
  template or a `computed`, so texts follow a language change.
