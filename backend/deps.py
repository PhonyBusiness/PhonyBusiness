"""Shared singletons used across main.py and the routers."""

from backend.config import get_settings
from backend.database import MongoDatabase

settings = get_settings()
mongo = MongoDatabase(settings.mongodb_uri)
