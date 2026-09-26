from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Settings:
    """Runtime settings for provider and database integrations."""

    def __init__(self) -> None:
        self.mongodb_uri = os.getenv("MONGODB_URI", "").strip()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        self.elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID", "").strip()
        self.safe_word = os.getenv("SAFE_WORD", "pineapple").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
