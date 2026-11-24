from fastapi import FastAPI, Response, status

from app.database import is_database_reachable

app = FastAPI(title="IApply API")


@app.get("/health")
def health(response: Response) -> dict[str, str]:
    """Lets Docker, the frontend or a human check that the API and its database are up."""
    if not is_database_reachable():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}
