from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlmodel import Session, col, select

from app.collection import CollectionResult, collect_jobs
from app.database import get_session, is_database_reachable
from app.models import JobOffer

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
    """The offers still to look at (not hidden), most recent first."""
    query = (
        select(JobOffer)
        .where(col(JobOffer.hidden).is_(False))
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
