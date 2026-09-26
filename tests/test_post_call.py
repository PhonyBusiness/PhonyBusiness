"""Post-call webhook parsing and signature checks."""

import hashlib
import hmac
import json
from pathlib import Path

from bson import ObjectId

from backend.post_call import build_conversation, split_flags, verify_signature

FIXTURE = Path(__file__).parent / "fixtures" / "post_call_webhook.json"


def load_payload() -> dict:
    return json.loads(FIXTURE.read_text())


def test_conversation_keeps_results_not_conversation_text():
    stored = json.dumps(build_conversation(load_payload()), default=str)
    for private in ("Resident Name", "User line", "Agent line", "must not be stored"):
        assert private not in stored


def test_outcome_comes_from_the_record_outcome_tool_call():
    outcome = build_conversation(load_payload())["outcome"]
    assert outcome == {
        "result": "pass",
        "flags": ["Urgency or threat of losing benefits", "Requests a Social Security number"],
        "turn": 5,
        "decided_at_secs": 91,
    }


def test_timing_sentiment_latency_and_cost():
    conversation = build_conversation(load_payload())
    assert conversation["conversation_id"] == "conv_test_1"
    assert conversation["started_at"].isoformat() == "2026-09-26T19:19:10+00:00"
    assert conversation["duration_secs"] == 136
    assert conversation["turns"] == {"agent": 4, "user": 3}
    assert conversation["sentiment"]["peak_frustration"] == 0.3
    assert [p["frustration"] for p in conversation["timeline"] if "frustration" in p] == [0.0, 0.3]
    assert conversation["latency"] == {"llm_ttfb_avg_secs": 2.6, "llm_ttfb_max_secs": 5.0, "fallback_turns": 1}
    assert conversation["cost"]["credits"] == 925
    assert conversation["usage"]["models"]["gemini-2.5-flash"] == {"input_tokens": 2217, "output_tokens": 112}


def test_scenario_falls_back_to_persona_match_and_call_wins_when_present():
    assert build_conversation(load_payload())["scenario_name"] == "benefits_imposter"

    call = {"_id": ObjectId(), "scenario_name": "tech_support", "dynamic_variables": {"difficulty": "hard"}}
    conversation = build_conversation(load_payload(), call)
    assert conversation["scenario_name"] == "tech_support"
    assert conversation["difficulty"] == "hard"
    assert conversation["call_id"] == str(call["_id"])


def test_split_flags_accepts_string_or_list():
    assert split_flags("a, b ,,c") == ["a", "b", "c"]
    assert split_flags(["a", " b "]) == ["a", "b"]
    assert split_flags(None) == []


def sign(body: bytes, secret: str, timestamp: int) -> str:
    digest = hmac.new(secret.encode(), f"{timestamp}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
    return f"t={timestamp},v0={digest}"


def test_signature_accepts_valid_and_rejects_tampered_or_stale():
    body = b'{"type": "post_call_transcription"}'
    header = sign(body, "secret", 1_000_000)
    assert verify_signature(body, header, "secret", now=1_000_010)
    assert not verify_signature(body + b" ", header, "secret", now=1_000_010)
    assert not verify_signature(body, header, "other", now=1_000_010)
    assert not verify_signature(body, header, "secret", now=1_000_000 + 3600)
    assert not verify_signature(body, None, "secret")
    assert not verify_signature(body, "garbage", "secret")
