"""FastAPI entry point for PhonyBusiness."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.deps import mongo
from backend.routers import calls, tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open and verify external connections when the API process starts."""
    mongo.connect()
    app.state.mongo = mongo
    try:
        yield
    finally:
        mongo.close()


app = FastAPI(title="PhonyBusiness API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process and database connection are running."""
    return {
        "status": "ok",
        "mongodb": "connected" if mongo.is_connected else "disconnected",
    }


app.include_router(calls.router)
app.include_router(tools.router)
