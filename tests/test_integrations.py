"""Read-only live checks. Run with RUN_INTEGRATION_TESTS=1 uv run pytest -v.

No calls, messages, generations, or database writes are performed.
Normal pytest runs skip these tests so credentials and network are optional.
"""

import os
import re
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest
from dotenv import dotenv_values
from pymongo import MongoClient

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 to run live integration checks",
)


@pytest.fixture(scope="module")
def config():
    # Read the project's .env regardless of the current working directory.
    # Explicit shell variables take precedence; never print values.
    return {
        **dotenv_values(Path(__file__).resolve().parents[1] / ".env"),
        **os.environ,
    }


def required(config, name):
    value = (config.get(name) or "").strip()
    if not value:
        pytest.fail(f"Missing {name}: set it in .env", pytrace=False)
    return value


def get_json(service, url, **kwargs):
    try:
        response = httpx.get(url, timeout=15, follow_redirects=False, **kwargs)
    except Exception:
        # Exception text may contain credentials, URLs, or phone numbers.
        pytest.fail(f"{service}: request failed; check network and configuration", pytrace=False)
    if response.status_code != 200:
        if service == "ElevenLabs user":
            try:
                detail = response.json().get("detail", {})
            except (ValueError, AttributeError):
                detail = {}
            if isinstance(detail, dict) and detail.get("status") == "missing_permissions":
                pytest.fail(
                    "ElevenLabs user: key lacks user_read permission; enable user read "
                    "access to run this profile check. Agent access is tested separately.",
                    pytrace=False,
                )
        hints = {
            401: "check credentials",
            403: "check API key permissions and account access",
            404: "check resource ID and account ownership",
            429: "rate limit or quota reached; retry later",
        }
        hint = hints.get(response.status_code, "check provider status and configuration")
        pytest.fail(f"{service}: HTTP {response.status_code}; {hint}", pytrace=False)
    try:
        data = response.json()
    except ValueError:
        pytest.fail(f"{service}: response was not JSON", pytrace=False)
    if not isinstance(data, dict):
        pytest.fail(f"{service}: unexpected response format", pytrace=False)
    return data


def twilio_auth(config):
    sid = required(config, "TWILIO_ACCOUNT_SID")
    if not re.fullmatch(r"AC[0-9a-fA-F]{32}", sid):
        pytest.fail("TWILIO_ACCOUNT_SID must be an AC account SID", pytrace=False)
    return sid, required(config, "TWILIO_AUTH_TOKEN")


def test_mongodb_connection(config):
    uri = required(config, "MONGODB_URI")
    try:
        with MongoClient(
            uri, serverSelectionTimeoutMS=10000, connectTimeoutMS=10000,
            socketTimeoutMS=10000, timeoutMS=15000,
        ) as client:
            result = client.admin.command("ping")
    except Exception:
        pytest.fail(
            "MongoDB: connection failed; check URI, credentials, TLS, and Atlas IP access list",
            pytrace=False,
        )
    if result.get("ok") != 1:
        pytest.fail("MongoDB: ping was not successful", pytrace=False)


def test_twilio_account(config):
    auth = twilio_auth(config)
    data = get_json(
        "Twilio account",
        f"https://api.twilio.com/2010-04-01/Accounts/{auth[0]}.json",
        auth=auth,
    )
    if data.get("status") != "active":
        pytest.fail("Twilio account is not active", pytrace=False)


def test_twilio_phone_number(config):
    auth = twilio_auth(config)
    phone = required(config, "TWILIO_PHONE_NUMBER")
    if not re.fullmatch(r"\+[1-9]\d{1,14}", phone):
        pytest.fail("TWILIO_PHONE_NUMBER must use E.164 format (e.g. +15551234567)", pytrace=False)
    data = get_json(
        "Twilio phone number",
        f"https://api.twilio.com/2010-04-01/Accounts/{auth[0]}/IncomingPhoneNumbers.json",
        auth=auth, params={"PhoneNumber": phone, "PageSize": 1},
    )
    numbers = data.get("incoming_phone_numbers", [])
    match = next((n for n in numbers if n.get("phone_number") == phone), None)
    if match is None:
        pytest.fail("Configured phone number is not owned by this Twilio account", pytrace=False)
    capabilities = match.get("capabilities", {})
    if not capabilities.get("voice") or not capabilities.get("sms"):
        pytest.fail("Configured Twilio number must support both voice and SMS", pytrace=False)


def test_twilio_verify_service(config):
    auth = twilio_auth(config)
    sid = required(config, "TWILIO_VERIFY_SERVICE_SID")
    if not re.fullmatch(r"VA[0-9a-fA-F]{32}", sid):
        pytest.fail("TWILIO_VERIFY_SERVICE_SID must be a VA service SID", pytrace=False)
    data = get_json("Twilio Verify", f"https://verify.twilio.com/v2/Services/{sid}", auth=auth)
    if data.get("sid") != sid:
        pytest.fail("Twilio Verify: unexpected service response", pytrace=False)


def test_elevenlabs_api_key(config):
    get_json(
        "ElevenLabs user",
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": required(config, "ELEVENLABS_API_KEY")},
    )


def test_elevenlabs_agent(config):
    agent_id = required(config, "ELEVENLABS_AGENT_ID")
    data = get_json(
        "ElevenLabs agent",
        f"https://api.elevenlabs.io/v1/convai/agents/{quote(agent_id, safe='')}",
        headers={"xi-api-key": required(config, "ELEVENLABS_API_KEY")},
    )
    if data.get("agent_id") != agent_id:
        pytest.fail("ElevenLabs: unexpected agent response", pytrace=False)


def test_gemini_api_key(config):
    data = get_json(
        "Gemini",
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": required(config, "GEMINI_API_KEY")},
        params={"pageSize": 1},
    )
    if not data.get("models"):
        pytest.fail("Gemini: no models returned", pytrace=False)
