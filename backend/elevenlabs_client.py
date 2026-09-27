"""Minimal client for the ElevenLabs Conversational AI signed-URL endpoint."""

import httpx

SIGNED_URL_ENDPOINT = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"


class ElevenLabsError(RuntimeError):
    """Raised when the ElevenLabs API call fails or is misconfigured."""


def get_signed_url(agent_id: str, api_key: str) -> str:
    if not agent_id or not api_key:
        raise ElevenLabsError("ELEVENLABS_AGENT_ID or ELEVENLABS_API_KEY is not set")

    response = httpx.get(
        SIGNED_URL_ENDPOINT,
        params={"agent_id": agent_id},
        headers={"xi-api-key": api_key},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise ElevenLabsError(
            f"ElevenLabs signed URL request failed: {response.status_code} {response.text}"
        )

    signed_url = response.json().get("signed_url")
    if not signed_url:
        raise ElevenLabsError("ElevenLabs response was missing signed_url")

    return signed_url
