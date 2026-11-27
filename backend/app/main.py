from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import case
from sqlmodel import Session, and_, col, or_, select

from app.collection import CollectionResult, collect_jobs
from app.cover_letter import (
    MissingBackgroundError,
    MissingOfferTextError,
    RevisedLetter,
    check_can_write,
    generate_letter,
    get_letter,
    revise_letter,
    save_letter,
)
from app.database import get_session, is_database_reachable
from app.llm import (
    PROVIDERS,
    effective_model,
    get_chat_model,
    get_settings,
    guess_provider,
    read_api_key,
    save_api_key,
)
from app.manual_offer import DuplicateOfferError, ExtractedOffer, extract_offer, save_manual_offer
from app.models import (
    Application,
    ApplicationWithJob,
    CoverLetter,
    CoverLetterChange,
    CoverLetterExample,
    CoverLetterRevision,
    DescriptionChange,
    JobOffer,
    LetterExampleChange,
    LlmSettings,
    LlmSettingsChange,
    LlmSettingsView,
    ManualOfferCreate,
    ManualOfferText,
    ProfileChange,
    ProviderInfo,
    StatusChange,
    UserProfile,
    utc_now,
)
from app.tracking import close_stale_applications

app = FastAPI(title="IApply API")

SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/health")
def health(response: Response) -> dict[str, str]:
    """Lets Docker, the frontend or a human check that the API and its database are up."""
    if not is_database_reachable():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}


@app.post("/jobs/collect")
def collect(session: SessionDep) -> CollectionResult:
    """Fetch the offers published since the last collection, from every source."""
    return collect_jobs(session)


def score_threshold(profile: UserProfile):
    """The threshold of each offer, as a SQL expression: full remote offers have their own one."""
    return case(
        (col(JobOffer.remote).is_(True), profile.min_score_remote),
        else_=profile.min_score_onsite,
    )


@app.get("/jobs")
def list_jobs(session: SessionDep) -> list[JobOffer]:
    """The offers still to look at (neither hidden nor applied to), most interesting first.

    Offers scored under their profile threshold (remote or on-site) are left out,
    unless the user restored them.
    Offers not scored yet come first,
    so the user sees them; then the highest scores, then the most recent.
    """
    applied_ids = select(Application.job_offer_id)
    threshold = score_threshold(get_the_profile(session))
    query = (
        select(JobOffer)
        .where(col(JobOffer.hidden).is_(False))
        .where(col(JobOffer.id).not_in(applied_ids))
        .where(
            or_(
                col(JobOffer.score).is_(None),
                col(JobOffer.score) >= threshold,
                col(JobOffer.restored).is_(True),
            )
        )
        .order_by(col(JobOffer.score).desc().nulls_first(), col(JobOffer.published_at).desc())
    )
    return list(session.exec(query).all())


# The rejected offers page only shows the last week: older ones would make it grow forever.
REJECTED_OFFERS_DAYS = 7


@app.get("/jobs/rejected")
def list_rejected_jobs(session: SessionDep) -> list[JobOffer]:
    """The offers left out of the list (hidden by the user, or scored under their threshold and not
    restored), published in the last week, sorted like the list. Applied offers are not rejected."""
    applied_ids = select(Application.job_offer_id)
    threshold = score_threshold(get_the_profile(session))
    under_threshold = and_(
        col(JobOffer.score) < threshold,  # an unscored offer is never under the threshold
        col(JobOffer.restored).is_(False),
    )
    query = (
        select(JobOffer)
        .where(col(JobOffer.id).not_in(applied_ids))
        .where(col(JobOffer.published_at) >= utc_now() - timedelta(days=REJECTED_OFFERS_DAYS))
        .where(or_(col(JobOffer.hidden).is_(True), under_threshold))
        .order_by(col(JobOffer.score).desc().nulls_first(), col(JobOffer.published_at).desc())
    )
    return list(session.exec(query).all())


def get_job_or_404(session: Session, job_id: int) -> JobOffer:
    job = session.get(JobOffer, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")
    return job


@app.post("/jobs/{job_id}/hide", status_code=status.HTTP_204_NO_CONTENT)
def hide_job(job_id: int, session: SessionDep) -> None:
    """Remove an offer from the list. It stays in the database so a collection does not bring it back."""
    job = get_job_or_404(session, job_id)
    job.hidden = True
    session.add(job)
    session.commit()


@app.post("/jobs/{job_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_job(job_id: int, session: SessionDep) -> None:
    """Bring a rejected offer back to the list, whatever the reason it left: hidden or low score."""
    job = get_job_or_404(session, job_id)
    job.hidden = False
    job.restored = True
    session.add(job)
    session.commit()


@app.post("/jobs/{job_id}/apply")
def apply_to_job(job_id: int, session: SessionDep) -> Application:
    """Record that the user applied to an offer: it leaves the list and goes to the tracking."""
    job = get_job_or_404(session, job_id)
    existing = session.exec(select(Application).where(Application.job_offer_id == job.id)).first()
    if existing is not None:
        return existing  # a double click must not fail nor create a second application
    application = Application(job_offer_id=job.id)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


@app.put("/jobs/{job_id}/description")
def change_description(job_id: int, change: DescriptionChange, session: SessionDep) -> JobOffer:
    """Save the full offer text pasted by the user. An empty text clears it."""
    job = get_job_or_404(session, job_id)
    job.description = change.description.strip() or None
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@app.post("/jobs/manual/extract")
def extract_manual_offer(pasted: ManualOfferText, session: SessionDep) -> ExtractedOffer:
    """Read the fields of a pasted offer with the LLM. Nothing is saved: the user checks them first."""
    try:
        return extract_offer(get_chat_model(get_settings(session)), pasted.text)
    except Exception as error:  # no LLM set up, or a provider error (bad key, quota...): shown as it is
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read the offer: {error}"
        ) from error


@app.post("/jobs/manual", status_code=status.HTTP_201_CREATED)
def add_manual_offer(new_offer: ManualOfferCreate, session: SessionDep) -> JobOffer:
    """Save an offer added by hand, once the user has checked its fields. It is never scored."""
    try:
        return save_manual_offer(session, new_offer)
    except DuplicateOfferError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


def get_letter_or_404(session: Session, job: JobOffer) -> CoverLetter:
    letter = get_letter(session, job)
    if letter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cover letter for this offer yet")
    return letter


@app.get("/jobs/{job_id}/cover-letter")
def read_cover_letter(job_id: int, session: SessionDep) -> CoverLetter:
    """The letter of the offer. 404 until one is generated."""
    return get_letter_or_404(session, get_job_or_404(session, job_id))


@app.post("/jobs/{job_id}/cover-letter")
def write_cover_letter(job_id: int, session: SessionDep) -> CoverLetter:
    """Ask the LLM for a letter for the offer, and save it. Replaces the letter there was."""
    job = get_job_or_404(session, job_id)
    try:
        check_can_write(session, job)  # checked first: no LLM set up is a less useful message
    except (MissingOfferTextError, MissingBackgroundError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    try:
        return generate_letter(session, get_chat_model(get_settings(session)), job)
    except Exception as error:  # no LLM set up, or a provider error (bad key, quota...): shown as it is
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not write the letter: {error}"
        ) from error


@app.put("/jobs/{job_id}/cover-letter")
def change_cover_letter(job_id: int, change: CoverLetterChange, session: SessionDep) -> CoverLetter:
    """Save the letter as changed by hand by the user."""
    job = get_job_or_404(session, job_id)
    get_letter_or_404(session, job)  # a letter is generated first: there is nothing to change before
    return save_letter(session, job, change.text)


@app.post("/jobs/{job_id}/cover-letter/revise")
def revise_cover_letter(job_id: int, revision: CoverLetterRevision, session: SessionDep) -> RevisedLetter:
    """Have the LLM make the asked changes, by replacing passages of the letter, and save the result."""
    job = get_job_or_404(session, job_id)
    get_letter_or_404(session, job)  # a letter is generated first
    try:
        model = get_chat_model(get_settings(session))
        return revise_letter(session, model, job, revision.text.strip(), revision.instructions.strip())
    except Exception as error:  # no LLM set up, or a provider error (bad key, quota...): shown as it is
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not change the letter: {error}"
        ) from error


@app.get("/applications")
def list_applications(session: SessionDep) -> list[ApplicationWithJob]:
    """The applications with their offer, most recent first, for the tracking page."""
    close_stale_applications(session)
    query = (
        select(Application, JobOffer)
        .join(JobOffer, col(Application.job_offer_id) == col(JobOffer.id))
        .order_by(col(Application.applied_at).desc())
    )
    return [with_job(application, job) for application, job in session.exec(query).all()]


def with_job(application: Application, job: JobOffer) -> ApplicationWithJob:
    # job_offer_id is left out: it would repeat job.id.
    return ApplicationWithJob(**application.model_dump(exclude={"job_offer_id"}), job=job)


def get_application_or_404(session: Session, application_id: int) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


def record_news(session: Session, application: Application) -> ApplicationWithJob:
    """Save the application with `last_news_at` set to now, and return it with its offer."""
    application.last_news_at = utc_now()
    session.add(application)
    session.commit()
    session.refresh(application)
    return with_job(application, get_job_or_404(session, application.job_offer_id))


@app.put("/applications/{application_id}/status")
def change_status(application_id: int, change: StatusChange, session: SessionDep) -> ApplicationWithJob:
    """Set a new status. A status change is news too, so the month without news starts again."""
    application = get_application_or_404(session, application_id)
    application.status = change.status
    return record_news(session, application)


@app.post("/applications/{application_id}/news")
def got_news(application_id: int, session: SessionDep) -> ApplicationWithJob:
    """The "I got news" button: the status stays the same, but the month without news starts again."""
    return record_news(session, get_application_or_404(session, application_id))


# There is only one user, so one profile: the row with this id, created by a migration.
PROFILE_ID = 1


def get_the_profile(session: Session) -> UserProfile:
    return session.get_one(UserProfile, PROFILE_ID)


# The id is left out of the answers: there is only one profile, the frontend has no use for it.
@app.get("/profile", response_model_exclude={"id"})
def get_profile(session: SessionDep) -> UserProfile:
    """What the user is looking for. Empty until the first save."""
    return get_the_profile(session)


@app.put("/profile", response_model_exclude={"id"})
def change_profile(change: ProfileChange, session: SessionDep) -> UserProfile:
    """Save what the user is looking for, their background and the score thresholds."""
    profile = get_the_profile(session)
    profile.looking_for = change.looking_for.strip()
    if change.background is not None:
        profile.background = change.background.strip()
    if change.min_score_onsite is not None:
        profile.min_score_onsite = change.min_score_onsite
    if change.min_score_remote is not None:
        profile.min_score_remote = change.min_score_remote
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@app.get("/letter-examples")
def list_letter_examples(session: SessionDep) -> list[CoverLetterExample]:
    """The cover letters the user already wrote, in the order they were added."""
    return list(session.exec(select(CoverLetterExample).order_by(col(CoverLetterExample.id))).all())


@app.post("/letter-examples", status_code=status.HTTP_201_CREATED)
def add_letter_example(change: LetterExampleChange, session: SessionDep) -> CoverLetterExample:
    example = CoverLetterExample(title=change.title.strip(), text=change.text.strip())
    session.add(example)
    session.commit()
    session.refresh(example)
    return example


def get_letter_example_or_404(session: Session, example_id: int) -> CoverLetterExample:
    example = session.get(CoverLetterExample, example_id)
    if example is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Letter example not found")
    return example


@app.put("/letter-examples/{example_id}")
def change_letter_example(example_id: int, change: LetterExampleChange, session: SessionDep) -> CoverLetterExample:
    example = get_letter_example_or_404(session, example_id)
    example.title = change.title.strip()
    example.text = change.text.strip()
    session.add(example)
    session.commit()
    session.refresh(example)
    return example


@app.delete("/letter-examples/{example_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_letter_example(example_id: int, session: SessionDep) -> None:
    """A real delete: an example is the user's own text, nothing brings it back like a collection would."""
    session.delete(get_letter_example_or_404(session, example_id))
    session.commit()


def settings_view(settings: LlmSettings) -> LlmSettingsView:
    key = read_api_key()
    return LlmSettingsView(
        provider=settings.provider,
        model=effective_model(settings),
        api_key_hint=f"…{key[-4:]}" if key else None,
        providers=[ProviderInfo(id=provider_id, **info) for provider_id, info in PROVIDERS.items()],
    )


@app.get("/llm")
def get_llm_settings(session: SessionDep) -> LlmSettingsView:
    """The chosen provider and model, and whether a key is saved."""
    return settings_view(get_settings(session))


@app.put("/llm")
def change_llm_settings(change: LlmSettingsChange, session: SessionDep) -> LlmSettingsView:
    """Save the fields that were sent. The key goes to the local .env file, never to the database."""
    settings = get_settings(session)
    if change.api_key and change.api_key.strip():
        api_key = change.api_key.strip()
        save_api_key(api_key)
        if not change.provider:
            settings.provider = guess_provider(api_key) or settings.provider
    if change.provider:
        if change.provider not in PROVIDERS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown provider")
        if change.provider != settings.provider:
            settings.model = None  # a model name of one provider means nothing to another
        settings.provider = change.provider
    if change.model is not None:
        settings.model = change.model.strip() or None
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings_view(settings)


@app.post("/llm/test")
def test_llm_settings(session: SessionDep) -> dict[str, str]:
    """Send a tiny prompt to check that the provider, the model and the key work together."""
    try:
        get_chat_model(get_settings(session)).invoke("Just reply OK.")
    except Exception as error:  # any provider error (bad key, unknown model, quota) is shown as it is
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not reach the model: {error}"
        ) from error
    return {"status": "ok"}
