"""Shared fixtures: the API wired to an in-memory MongoDB instead of Atlas."""

import mongomock
import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.database import MongoDatabase


@pytest.fixture
def mongo(monkeypatch):
    database = MongoDatabase("mongodb://test")
    database.client = mongomock.MongoClient()
    monkeypatch.setattr(main, "mongo", database)
    return database


@pytest.fixture
def client(mongo, monkeypatch):
    monkeypatch.setattr(main.settings, "elevenlabs_webhook_secret", "")
    # No context manager: skips the lifespan hook, so no Atlas connection is attempted.
    return TestClient(main.app)
