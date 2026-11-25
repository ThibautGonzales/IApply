from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlmodel import Session, col, select

from app.collection import CollectionResult, collect_jobs
from app.database import get_session, is_database_reachable
from app.models import Application, ApplicationWithJob, JobOffer

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
    """The offers still to look at (neither hidden nor applied to), most recent first."""
    applied_ids = select(Application.job_offer_id)
    query = (
        select(JobOffer)
        .where(col(JobOffer.hidden).is_(False))
        .where(col(JobOffer.id).not_in(applied_ids))
        .order_by(col(JobOffer.published_at).desc())
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


@app.get("/applications")
def list_applications(session: SessionDep) -> list[ApplicationWithJob]:
    """The applications with their offer, most recent first, for the tracking page."""
    query = (
        select(Application, JobOffer)
        .join(JobOffer, col(Application.job_offer_id) == col(JobOffer.id))
        .order_by(col(Application.applied_at).desc())
    )
    return [
        ApplicationWithJob(**application.model_dump(exclude={"job_offer_id"}), job=job)
        for application, job in session.exec(query).all()
    ]
