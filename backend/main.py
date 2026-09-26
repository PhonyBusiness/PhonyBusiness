"""FastAPI entry point for ScamShield."""

from fastapi import FastAPI

app = FastAPI(title="ScamShield API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
