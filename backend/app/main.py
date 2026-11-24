from fastapi import FastAPI

app = FastAPI(title="IApply API")


@app.get("/health")
def health() -> dict[str, str]:
    """Lets Docker, the frontend or a human check that the API is up."""
    return {"status": "ok"}
