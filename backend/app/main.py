from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlmodel import Session, col, or_, select

from app.collection import CollectionResult, collect_jobs
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
from app.models import (
    Application,
    ApplicationWithJob,
    DescriptionChange,
    JobOffer,
    LlmSettings,
    LlmSettingsChange,
    LlmSettingsView,
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


@app.get("/jobs")
def list_jobs(session: SessionDep) -> list[JobOffer]:
    """The offers still to look at (neither hidden nor applied to), most interesting first.

    Offers scored under the profile threshold are left out, unless the user restored them.
    Offers not scored yet come first,
    so the user sees them; then the highest scores, then the most recent.
    """
    applied_ids = select(Application.job_offer_id)
    min_score = get_the_profile(session).min_score
    query = (
        select(JobOffer)
        .where(col(JobOffer.hidden).is_(False))
        .where(col(JobOffer.id).not_in(applied_ids))
        .where(
            or_(
                col(JobOffer.score).is_(None),
                col(JobOffer.score) >= min_score,
                col(JobOffer.restored).is_(True),
            )
        )
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
    """Save what the user is looking for and the score threshold."""
    profile = get_the_profile(session)
    profile.looking_for = change.looking_for.strip()
    if change.min_score is not None:
        profile.min_score = change.min_score
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


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
