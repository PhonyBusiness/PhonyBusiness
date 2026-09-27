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
        # Unset only in local development; the webhook then skips signature checks.
        self.elevenlabs_webhook_secret = os.getenv("ELEVENLABS_WEBHOOK_SECRET", "").strip()
        # Breakdowns with fewer calls than this are hidden so no resident can be singled out.
        self.analytics_min_group_size = int(os.getenv("ANALYTICS_MIN_GROUP_SIZE", "5"))
        # Post-call scoring; leave the key unset to skip scoring.
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        # Testing only: SCORING_PROVIDER=openai scores with any OpenAI-compatible API (e.g. Groq).
        self.scoring_provider = os.getenv("SCORING_PROVIDER", "gemini").strip().lower()
        self.scoring_base_url = os.getenv("SCORING_BASE_URL", "").strip()
        self.scoring_api_key = os.getenv("SCORING_API_KEY", "").strip()
        self.scoring_model = os.getenv("SCORING_MODEL", "").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
