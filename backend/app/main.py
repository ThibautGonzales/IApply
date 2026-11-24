from typing import Annotated

from fastapi import Depends, FastAPI, Response, status
from sqlmodel import Session, select

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
    """All saved offers, most recent first."""
    return list(session.exec(select(JobOffer).order_by(JobOffer.published_at.desc())).all())
