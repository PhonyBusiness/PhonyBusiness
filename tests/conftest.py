"""Shared fixtures: the API wired to an in-memory MongoDB instead of Atlas."""

import mongomock
import pytest
from fastapi.testclient import TestClient

from backend import deps, main
from backend.database import MongoDatabase
from backend.routers import analytics, calls, tools, webhooks


@pytest.fixture
def mongo(monkeypatch):
    database = MongoDatabase("mongodb://test")
    database.client = mongomock.MongoClient()
    # Each router imported `mongo` by name, so patch every module that holds it.
    for module in (deps, main, analytics, calls, tools, webhooks):
        monkeypatch.setattr(module, "mongo", database)
    return database


@pytest.fixture
def client(mongo, monkeypatch):
    monkeypatch.setattr(deps.settings, "elevenlabs_webhook_secret", "")
    # Never call the real Gemini API from tests; scoring tests mock it explicitly.
    monkeypatch.setattr(deps.settings, "gemini_api_key", "")
    monkeypatch.setattr(deps.settings, "scoring_provider", "gemini")
    # No context manager: skips the lifespan hook, so no Atlas connection is attempted.
    return TestClient(main.app)
