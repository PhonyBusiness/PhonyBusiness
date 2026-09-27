import json
from functools import lru_cache
from pathlib import Path

VOICES_FILE = Path(__file__).resolve().parent.parent / "scripts" / "voices" / "voices.json"


@lru_cache
def _voices() -> dict[str, str]:
    try:
        return json.loads(VOICES_FILE.read_text())
    except FileNotFoundError:
        return {}


def get_voice_id(scenario_name: str) -> str | None:
    """Voice for this scenario, or None to use the agent's default voice."""
    return _voices().get(scenario_name)