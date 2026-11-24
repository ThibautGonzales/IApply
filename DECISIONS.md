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

1. A "Collect" button fetches offers from the France Travail API, only those
   published since the last collection (about once a day).
2. The user's profile is pasted as plain text.
3. An LLM scores each offer against the profile; offers under a threshold are hidden.
4. Ranked list of offers with a direct link to each one.
5. Later: cover letter generation in the style of the user's existing letters.

## 2026-11-24 — Frontend to backend calls

- **The frontend calls `/api/...` on its own origin.** In Docker, nginx forwards
  `/api/` to the backend; with `ng serve`, `proxy.conf.json` does the same. The
  browser only ever talks to one origin, so no CORS setup is needed.
