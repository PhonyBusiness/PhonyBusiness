"""Post-call scoring with Gemini.

After a call ends, the transcript is redacted (numbers, the resident's name,
emails) and sent to Gemini, which rates how the resident handled the call and
lists what they gave away. Only the rating is stored; the redacted transcript
is never saved.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone

import httpx

from backend.post_call import dynamic_variables

logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
RATINGS = ("pass", "caution", "fail")
# Gemini sometimes answers 429/503 when busy; retry those with a short backoff.
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_DELAYS_SECS = (1, 2)
DISCLOSURES = (
    "ssn", "verification_code", "card_number", "account_pin", "bank_account",
    "gift_card", "agreed_to_pay", "personal_details", "none",
)

NUMBER_WORDS = (
    "zero|oh|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    "fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
    "sixty|seventy|eighty|ninety|hundred|thousand"
)
# Two or more number words in a row ("four five six"); a lone "one" stays readable.
SPOKEN_NUMBER = re.compile(rf"\b(?:{NUMBER_WORDS})(?:[\s,\-]+(?:{NUMBER_WORDS}))+\b", re.IGNORECASE)
DIGITS = re.compile(r"[+(]?\d(?:[\d\s().\-/]*\d)?")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

INSTRUCTIONS = """You grade a practice phone call from a scam-awareness training program.
An AI played a scammer; a resident answered. Grade only the resident's behavior
before the caller revealed it was a practice call. The transcript is redacted:
[number], [name], and [email] replace what was said.

Ratings:
- pass: refused, hung up, or said they would verify through an official channel.
- caution: kept engaging or hesitated, or shared minor details, but gave nothing sensitive and did not agree to pay.
- fail: disclosed anything sensitive or agreed to pay.

disclosed: what the resident gave or started to give, or ["none"].
spotted_red_flags: red flags from the provided list that the resident questioned or reacted to.
reason: one or two plain sentences for the resident; never repeat personal details."""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "rating": {"type": "STRING", "enum": list(RATINGS)},
        "disclosed": {"type": "ARRAY", "items": {"type": "STRING", "enum": list(DISCLOSURES)}},
        "spotted_red_flags": {"type": "ARRAY", "items": {"type": "STRING"}},
        "reason": {"type": "STRING"},
    },
    "required": ["rating", "disclosed", "spotted_red_flags", "reason"],
}


def redact(text: str, first_name: str | None = None) -> str:
    """Replace the resident's name, emails, and numbers (digits or spoken) with placeholders."""
    text = EMAIL.sub("[email]", text)
    if first_name and len(first_name.strip()) >= 2:
        text = re.sub(rf"\b{re.escape(first_name.strip())}\b", "[name]", text, flags=re.IGNORECASE)
    text = SPOKEN_NUMBER.sub("[number]", text)
    return DIGITS.sub("[number]", text)


def redacted_transcript(payload: dict) -> str:
    data = payload.get("data") or {}
    first_name = dynamic_variables(data).get("first_name")
    lines = []
    for turn in data.get("transcript") or []:
        message = turn.get("message")
        if not message or turn.get("role") not in ("agent", "user"):
            continue
        speaker = "Caller" if turn["role"] == "agent" else "Resident"
        lines.append(f"{speaker}: {redact(message, first_name)}")
    return "\n".join(lines)


def build_request(transcript: str, scenario: dict | None, recorded_result: str | None) -> dict:
    context = [
        f"Scenario: {scenario['display_name'] if scenario else 'unknown'}",
        "Red flags: " + ("; ".join(scenario["red_flags"]) if scenario else "unknown"),
        f"Outcome the caller recorded during the call: {recorded_result or 'none'}",
        "",
        "Transcript:",
        transcript,
    ]
    return {
        "system_instruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": "\n".join(context)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
            "temperature": 0,
        },
    }


def parse_response(body: dict, scenario: dict | None) -> dict | None:
    """Validate Gemini's JSON; return None rather than store anything malformed."""
    try:
        result = json.loads(body["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None
    if not isinstance(result, dict) or result.get("rating") not in RATINGS:
        return None

    disclosed = [item for item in result.get("disclosed") or [] if item in DISCLOSURES and item != "none"]
    allowed_flags = set(scenario["red_flags"]) if scenario else set()
    spotted = [flag for flag in result.get("spotted_red_flags") or [] if flag in allowed_flags]
    return {
        "rating": result["rating"],
        "disclosed": disclosed,
        "spotted_red_flags": spotted,
        "reason": str(result.get("reason") or "")[:400],
    }


def score_call(payload: dict, scenario: dict | None, recorded_result: str | None,
               api_key: str, model: str) -> dict | None:
    """Rate one finished call. Returns None if Gemini isn't configured or the call fails."""
    if not api_key:
        return None
    transcript = redacted_transcript(payload)
    if not transcript:
        return None
    request = build_request(transcript, scenario, recorded_result)
    for attempt in range(len(RETRY_DELAYS_SECS) + 1):
        try:
            response = httpx.post(
                GEMINI_URL.format(model=model),
                headers={"x-goog-api-key": api_key},
                json=request,
                timeout=30.0,
            )
            response.raise_for_status()
            break
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            retryable = status in RETRY_STATUSES
            logger.warning("Gemini scoring failed with HTTP %s (attempt %s)", status, attempt + 1)
        except httpx.HTTPError as exc:
            retryable = True
            logger.warning("Gemini scoring request failed (%s, attempt %s)", type(exc).__name__, attempt + 1)
        if not retryable or attempt == len(RETRY_DELAYS_SECS):
            return None
        time.sleep(RETRY_DELAYS_SECS[attempt])

    result = parse_response(response.json(), scenario)
    if result is None:
        logger.warning("Gemini returned an unusable score")
        return None
    return result | {"model": model, "scored_at": datetime.now(timezone.utc)}
