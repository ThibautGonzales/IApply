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

## MVP scope (first version, replaced on 2026-11-25, see "Roadmap update")

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

## 2026-11-25 — Roadmap update

- **One job source: the Jooble API.** No scraping: it breaks whenever a site changes and
  is not something to publish on a public repository. Another API can be added later.
- **Offers can be added by hand.** The user pastes the text of an offer found elsewhere
  (LinkedIn...) and its link; an LLM fills the fields (title, company, location, contract,
  salary, remote). The offer is saved with `source = "manual"` and is then handled like the
  others (scoring, cover letter, tracking).
- **LLM scoring right after the offer actions and tracking.** A collection brings back far
  too many offers, most of them unrelated to the search; scoring them against the profile
  and showing only the relevant ones is what makes the app save time. Actions and tracking
  come just before because they are quick to build and useful at once.
- **Offer actions in the list:** generate a cover letter, hide, mark as applied. A hidden or
  applied offer leaves the list.
- **Hiding is a `hidden` flag on `JobOffer`, never a real delete**: a deleted offer would
  come back at the next collection.
- **Applications live in their own `Application` table**, linked to the offer (status,
  application date, last status change, notes later). It keeps the offer and the
  application apart, and the tracking page has its own data.
- **Tracking page:** applied offers with their status and a link to the original posting
  (useful before an interview). Statuses: waiting for an answer, interview, rejected,
  accepted, closed without answer.
- **Automatic closing:** an application with no status change for one month is considered
  closed without answer. Checked when the applications are read, no scheduled job.
- **Cover letters** stay in the style of the user's existing letters.

- **One route per action**: `POST /jobs/{id}/hide` and `POST /jobs/{id}/apply`, rather than a
  generic `PATCH /jobs/{id}`. The tracking page will get its own `/applications` routes.
- **Applying is idempotent**: applying twice returns the existing application (one per offer,
  enforced by a unique `job_offer_id`), so a double click cannot fail.
- **No undo button for now**: added if the need shows up.

## 2026-11-25 — Application tracking

- **Closed automatically after 30 days without news**, only while the status is "waiting" or
  "interview". Rejected, accepted and closed are final and never touched. The check is one
  `UPDATE` run by `GET /applications` (`app/tracking.py`).
- **`last_news_at` instead of `status_changed_at`**: a status change is news, and so is the
  "I got news" button (`POST /applications/{id}/news`), which keeps the status. Both restart
  the month. The page shows this date as "Last news".
- **`GET /applications` returns each application with its offer nested** (`ApplicationWithJob`),
  in one request. The action routes return the same shape, so the page replaces one row
  instead of reloading the list.
- **Statuses are a `StrEnum` (`ApplicationStatus`)**: stored as plain text, validated by
  FastAPI on `PUT /applications/{id}/status` (422 for an unknown status).
- **Two pages with the Angular router**: `/` for the offers, `/applications` for the tracking,
  with a menu in the header. `jobs.ts` and `job-table.ts` keep their logic.
- **"View offer" unfolds the saved details under the row** (location, contract, salary,
  description) with a link to the original posting. Jooble only gives a snippet of the
  description; getting the full text is a later topic.

### Roadmap (one branch and one pull request each)

1. `docs/updateRoadmap`: this update.
2. `feat/offerActions`: hide and mark as applied from the list.
3. `feat/applicationTracking`: tracking page, statuses, automatic closing, link.
4. `feat/userProfile`: the user's profile as plain text.
5. `feat/offerScoring`: LLM score against the profile, only relevant offers shown.
6. `feat/manualOffer`: paste an offer, the LLM fills its fields.
7. `feat/coverLetter`: cover letter generation.
8. Later: search settings screen, a second job API.
