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
- **Sources are plain modules exposing `fetch_jobs(session, since) -> list[JobOffer]`** (the
  session was added with "Jooble searches worked out by the LLM"), registered
  in `app/sources/__init__.py` (`SOURCES`). Simpler than an abstract class while there is
  one source.
- **"Since the last collection" = day of the most recent saved offer** of that source
  (7 days back the first time). No extra table; offers fetched twice are skipped thanks to
  the unique (`source`, `external_id`) constraint and a check before saving.
- **Jooble's date filter is not trusted**: it can return months-old offers, so older offers
  are dropped in our code.
- **Search settings are environment variables** (`JOOBLE_*` in `.env`) until a settings
  screen exists (replaced on 2026-11-27, see "Jooble searches worked out by the LLM"). Remote offers are a second search per keyword with the location
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
  description; getting the full text is a later topic (see "Full offer text" below).

### Roadmap (one branch and one pull request each)

1. `docs/updateRoadmap`: this update.
2. `feat/offerActions`: hide and mark as applied from the list.
3. `feat/applicationTracking`: tracking page, statuses, automatic closing, link.
4. `feat/userProfile`: the user's profile as plain text (done, see "User profile" below).
5. `feat/offerScoring`: LLM score against the profile, only relevant offers shown (done, see
   "LLM settings" and "Offer scoring" below).
6. `feat/manualOffer`: paste an offer, the LLM fills its fields (done, see "Offers added by hand" below).
7. `feat/coverLetter`: cover letter generation (done, see "Cover letters" below).
8. Later: a second job API.
9. `feat/llmJoobleSearches`: the LLM works out the Jooble searches from the profile (done, see
   "Jooble searches worked out by the LLM" below). It replaces the search settings screen.

## 2026-11-25 — Full offer text

- **The Jooble snippet is no longer saved.** It is cut at about 290 characters (275 on average
  in our database), too short to judge an offer. A migration emptied the snippets already saved.
- **No automatic fetch of the offer page.** The Jooble offer pages are behind a Cloudflare
  anti-bot check: the backend gets an HTTP 403 challenge page, not the offer. Getting around it
  would mean defeating that check, and it would break at each change on their side.
- **`description` now only holds the full text pasted by the user**, from the original posting
  opened in the browser. `PUT /jobs/{id}/description` saves it; an empty text clears it.
- **Paste from both pages**, in the shared `OfferDetails` component unfolded by "View offer":
  the text is needed before applying (cover letter) and stays useful after (interview).
- **LLM scoring works with the title, company, location and contract** of an offer, plus its
  description when the user has pasted one.

## 2026-11-26 — User profile

- **The profile is only "what I am looking for", as plain text** (`UserProfile.looking_for`): job,
  technologies, location, remote, contract, what to avoid. No CV: the scoring only sees the offer
  title, company, location and contract (plus the pasted text, when there is one), which say little
  about the technologies, so matching a CV against them would not help.
- **The profile filters the offers, it does not drive the Jooble search.** The search keeps its
  `JOOBLE_*` settings in `.env`. A later "Suggest" button may propose keywords from the profile
  (roadmap item 9). (Replaced on 2026-11-27: the profile now drives the search, see "Jooble searches
  worked out by the LLM".)
- **One user, so one row (id 1), created empty by a migration**: the profile always exists, and the
  routes only read and update it. The id stays inside the backend: `GET /profile` and `PUT /profile`
  take none and leave it out of their answer.
- **The row has its own migration** (`e5a7c9d1f3b4`), separate from the one creating the table: a
  migration already applied somewhere is never edited, since Alembic does not run it again.
- **Cover letter examples are not part of the profile**: they come with `feat/coverLetter` (see "Cover letters").

## 2026-11-26 — LLM settings

- **The user chooses the LLM on an "LLM" page**, the same way as in MorningDevNews: four providers
  (OpenAI, Anthropic, Google Gemini, Mistral), each with a default model (`app/llm.py`, `PROVIDERS`).
  The user can type another model: a stronger one costs more, a smaller one runs cheaper.
- **The API key never goes to the database.** It stays on the user's disk, in `backend/data/.env`
  (`LLM_API_KEY`), ignored by Git and by the Docker image, and mounted in the backend container so it
  survives a rebuild. The API never sends it back, only its last 4 characters.
- **Not the root `.env`**: Docker Compose reads that one; the backend does not rewrite a file it does
  not own.
- **The provider and the model are in `llm_settings`**, one row (id 1) created by its migration,
  like the profile. An empty model means the provider's default.
- **The provider is guessed from the key prefix** when none is chosen (`sk-ant-`, `AIza`, `sk-`).
  Changing provider forgets the typed model, which means nothing to another provider.
- **A "Test" button** (`POST /llm/test`) sends a tiny prompt and shows the provider's error as it is.
- **Tests never call a real LLM**: they use LangChain's `FakeListChatModel` and a temporary `.env`.

## 2026-11-26 — Offer scoring

- **A score from 0 to 100 per offer, with no reason.** A reason would cost output tokens for
  something the user does not read. `JobOffer.score` stays empty until the LLM has scored the offer.
- **The scale is written in the prompt** (`app/scoring.py`): 80-100 is the job the user would love,
  50-79 a job they look for too (a secondary wish, or part of the main one), under 50 not really
  what they look for. **50 is the yes/no line**; the scores also rank the offers.
- **The threshold is set by the user on the Profile page** (`UserProfile.min_score`, 50 by default).
  It is applied when the list is read, so changing it needs no new LLM call.
- **Scoring runs at the end of each collection**, on every offer of the list with no score yet
  (neither hidden nor applied to). Taking longer is fine: the goal is to save the user's time.
- **Never blocks the collection**: without an LLM, with an empty profile or on a provider error, the
  offers are saved unscored, the reason is shown, and the next collection tries again.
- **Scores are saved after each batch**: a provider error on a later batch keeps the scores already
  received, so they are not paid for twice.
- **nginx waits up to 10 minutes for the API** (`proxy_read_timeout 600s`): with the scoring, a
  collection can take minutes, and the 60 s default cut it while the backend went on.
- **Unscored offers stay in the list, at the top**: nothing disappears without the LLM's verdict.
  Then the list goes from the highest score to the lowest, then the most recent.
- **Batches of 20 offers per call**, one line per offer, and a **structured answer** (`OfferScores`, a
  list of id + score). We ask for the provider's own structured output (`method="json_schema"`),
  supported by the four providers: the answer is constrained to the schema while it is generated,
  then validated by Pydantic. No text is parsed. The default method (a forced tool call) is not
  forced on the newest Claude models and could come back without scores.
- **The migrations are new ones**: the default threshold went from 70 to 50 in a second migration,
  since the first one may already be applied.
- **Rejected offers** (scored under the threshold) get their own page, where one can be brought back
  to the list (see below).

## 2026-11-26 — Rejected offers page

- **A rejected offer is one left out of the list**: hidden by the user, or scored under the
  threshold. Both are on the same page, with a "Reason" column, so a "Hide" clicked by mistake can be
  undone too. Applied offers are never rejected: they are on the tracking page.
- **Bringing an offer back sets a new `restored` flag** (and clears `hidden`). The score is kept:
  clearing it would make the next collection score the offer again and reject it again. Lowering
  the threshold was not an option either: it brings back every offer, not one.
- **Only the last 7 days** (`REJECTED_OFFERS_DAYS`), on `published_at`, so the page does not grow
  forever. No new date column: an old offer hidden today by mistake does not show there.
- **The reason is not sent by the API**: the page reads `hidden` (otherwise the score is too low).
- **The page has its own small table** rather than a mode in `JobTable`: other columns and buttons,
  and `JobTable` stays simple.

## 2026-11-26 — Offers added by hand

- **Two steps: the LLM reads, the user checks, then saves.** `POST /jobs/manual/extract` sends the
  pasted text to the LLM and returns the fields (title, company, location, contract, salary, full
  remote) without saving anything; the page shows them in a form to correct; `POST /jobs/manual`
  saves the checked offer. An LLM mistake never reaches the database unseen.
- **Same structured output as the scoring** (`method="json_schema"`, `ExtractedOffer` in
  `app/manual_offer.py`). Every field is required in the schema and the LLM answers null for what the
  text does not say: some providers ask for required fields, and the prompt says never to guess.
- **The pasted text is saved as it is** as the offer `description`: the LLM does not rewrite it
  (fewer output tokens, and the user's text stays exact).
- **No new column, no migration**: `source = "manual"`, a random `external_id` (uuid) since the offer
  has no id in a source, and `published_at` = the day it is added, as a date read in the text would
  not be reliable.
- **The link is required, and one link can only be added once** among the manual offers (409).
  Collected offers are not checked, so a Jooble link never blocks a manual offer.
- **Offers added by hand are never scored.** Adding one means the user wants to see it. Unscored, it
  stays at the top of the list, where the user handles it first; the sort of the list is unchanged.
  `unscored_offers()` leaves them out, so no collection scores them later. The score column shows ✎.
- **A separate `AddOffer` component** on the offers page, which emits the saved offer (`added`): the
  offers page puts it first without reloading the list.

## 2026-11-26 — Remote and on-site thresholds

- **Two thresholds on the profile**: `min_score_onsite` and `min_score_remote` (0-100, 50 by default),
  replacing `min_score`. A full remote offer can be worth less of a match (or more) than one near home.
- **A new migration renames `min_score` to `min_score_onsite`** and copies its value into
  `min_score_remote`, so the list does not change until the user sets them apart. The migrations
  already applied are not edited.
- **"Remote" means `JobOffer.remote` is true** (full remote). The column is never null, so there is
  no unknown case: on-site, hybrid and offers whose remote status is not known use the on-site
  threshold.
- **One SQL `CASE` picks the threshold of each offer** (`score_threshold()` in `app/main.py`), used by
  both `GET /jobs` and its mirror `GET /jobs/rejected`, so the two lists cannot drift apart. Unscored
  offers (including the ones added by hand) are still never compared, and the sort is unchanged.

## 2026-11-27 — Cover letters

Cover letters are one of the main features of the app.

- **"My background" on the profile** (`UserProfile.background`): skills, career, work experience, as free
  text or a pasted CV. Only used for the letters; the scoring still uses `looking_for` only.
- **The letter examples have their own table** (`CoverLetterExample`: title, text) and their own page,
  "Letter examples", with add, edit and delete. The user plans 5 to 10 letters, too many for a section of
  the profile page. The title is only for the user: the LLM gets the texts only.
- **Deleting an example is a real delete**, unlike offers: it is the user's own text, nothing brings it
  back. The page asks for a second click instead of a browser `confirm()`.
- **What the examples say about the user is true, like the background**: the LLM follows their style and
  reuses their facts (skills, jobs, projects, results). Only what they say about the companies they were
  written for is not reused. It never claims a fact found neither in the background nor in the examples.
- **No letter without the offer text** (the button is greyed out): from a title alone, the letter could only
  be generic. Nor without a background *and* without any example: the LLM would have nothing true to say.
  Both are checked before any LLM call.
- **One letter per offer, in its own `CoverLetter` table** (unique `job_offer_id`), like `Application`. Writing
  a new letter replaces the text. The letter stays after applying, from the tracking page.
- **The letter is written in the language of the offer, as plain text**: one call, the whole answer is the
  letter, so no structured output. `answer.text` joins the parts some providers send as a list.
- **The letter has its own page** (`/jobs/:id/letter`), opened from "View offer": edit by hand (free), copy,
  ask the LLM for changes, or write a new letter (two clicks, it replaces everything). The page warns that
  many LLM requests can quickly cost money.
- **The LLM changes a letter with replacements, never by writing it again**: output tokens are the expensive
  ones. It answers a structured list of `{old, new}` (`LetterChanges`, `method="json_schema"` like the
  scoring), in one call, with no tools: tools would mean several calls and far more output tokens.
- **Our code applies the replacements** (`apply_replacements()`, a pure function, tested without LLM). A
  replacement whose `old` is missing, empty or found several times fails and changes nothing: replacing at
  the wrong place would be worse. The others are applied and saved; the failed ones are listed on the page.
- **The page sends the text it shows** with the instructions, so changes made by hand and not saved yet are
  not lost. The context is the same as for writing (profile, examples, offer) plus the letter.
- **`GET /jobs/{id}`** was added for the letter page, which can be opened from its own address.
- **The router gives `:id` to the page as an input** (`withComponentInputBinding()`), without `ActivatedRoute`.

## 2026-11-27 — Jooble searches worked out by the LLM

- **The LLM works out the Jooble searches from "What I am looking for" only**, not from the background:
  the job, the place and remote are written there. `JOOBLE_KEYWORDS`, `JOOBLE_LOCATION`,
  `JOOBLE_RADIUS_KM`, `JOOBLE_INCLUDE_REMOTE`, `JOOBLE_REMOTE_LOCATION` and `JOOBLE_REMOTE_KEYWORD` are
  gone; `.env` keeps only `JOOBLE_API_KEY` and `JOOBLE_HOST`. Without an LLM, there is no search: the app
  is LLM-assisted by design.
- **Worked out when the profile is saved, not at each collection**: one LLM call, stable searches, and the
  user sees them on the profile page. Only when "What I am looking for" changes (or there are no searches
  yet for a text): saving the background or a threshold costs no LLM call. An empty text clears them.
- **If the LLM fails, nothing is saved** (`PUT /profile` answers 400 with the reason): the profile and its
  searches always go together, in one commit, and the text stays in the box to try again.
- **Each search is complete**: keywords, and either a place with a radius or full remote
  (`JoobleSearch` table, `PlannedSearches` structured output, `method="json_schema"` like the scoring).
  More flexible than shared keywords with one place, e.g. one job searched remote only.
- **At most 6 searches** (`MAX_SEARCHES`), cut in our code, not only asked in the prompt: each search costs
  up to 5 calls of the 100 a day of the free key. A remote search loses any place the LLM gives.
- **The LLM does not know Jooble's "Télétravail" location**: it says "remote", `jooble.search_body()`
  turns it into that location (`REMOTE_LOCATION`).
- **Sources get the session** (`fetch_jobs(session, since)`) to read their settings from the database,
  rather than Jooble opening its own connection or the common collection code reading Jooble's searches.
- **Read-only on the profile page** (`GET /profile/searches`, separate from `GET /profile` so that answer
  keeps its shape): to change them, the user rewrites what they are looking for.
