"""Gemini post-call scoring: redaction, request shape, response validation, storage."""

import json
from pathlib import Path

import httpx
import pytest

from backend import deps, gemini_scoring
from backend.gemini_scoring import build_request, parse_response, redact, redacted_transcript, score_call
from backend.scenarios import get_scenario

FIXTURE = Path(__file__).parent / "fixtures" / "post_call_webhook.json"
SCENARIO = get_scenario("benefits_imposter")


def gemini_body(result: dict) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": json.dumps(result)}]}}]}


VALID = {
    "rating": "fail",
    "disclosed": ["ssn", "none"],
    "spotted_red_flags": ["Requests a Social Security number", "Made-up flag"],
    "reason": "You started reading your Social Security number.",
}


@pytest.mark.parametrize("text, expected", [
    ("Sure, it's 4 8 2 9 1 7", "Sure, it's [number]"),
    ("My social is 555-12-3456.", "My social is [number]."),
    ("It's four five six, seven eight", "It's [number]"),
    ("Hold on one moment", "Hold on one moment"),
    ("Email me at maria.g@gmail.com", "Email me at [email]"),
    ("Hi MARIA, is this Maria?", "Hi [name], is this [name]?"),
    ("Call (305) 555-0123 now", "Call [number] now"),
])
def test_redact(text, expected):
    assert redact(text, "Maria") == expected


def test_redacted_transcript_labels_speakers_and_skips_tool_turns():
    payload = json.loads(FIXTURE.read_text())
    payload["data"]["transcript"][1]["message"] = "Resident Name here, my code is 482917"
    transcript = redacted_transcript(payload)

    assert transcript.splitlines()[0] == "Caller: Agent line one."
    assert "Resident: [name] here, my code is [number]" in transcript
    assert "482917" not in transcript and "Resident Name" not in transcript
    assert len(transcript.splitlines()) == 7  # the record_outcome tool turn has no message


def test_request_carries_context_schema_and_no_raw_numbers():
    request = build_request("Resident: my code is [number]", SCENARIO, "fail")
    text = request["contents"][0]["parts"][0]["text"]
    assert "Benefits imposter" in text and "Requests a Social Security number" in text
    assert request["generationConfig"]["responseMimeType"] == "application/json"
    assert request["generationConfig"]["responseSchema"]["required"] == [
        "rating", "disclosed", "spotted_red_flags", "reason"]


def test_parse_keeps_only_known_values():
    assert parse_response(gemini_body(VALID), SCENARIO) == {
        "rating": "fail",
        "disclosed": ["ssn"],
        "spotted_red_flags": ["Requests a Social Security number"],
        "reason": "You started reading your Social Security number.",
    }


@pytest.mark.parametrize("body", [
    {},
    {"candidates": []},
    {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]},
    gemini_body({"rating": "excellent", "disclosed": [], "spotted_red_flags": [], "reason": ""}),
])
def test_parse_rejects_malformed(body):
    assert parse_response(body, SCENARIO) is None


def test_score_call_skips_without_key():
    assert score_call(json.loads(FIXTURE.read_text()), SCENARIO, "pass", "", "m") is None


def fake_post(status: int, body: dict):
    def post(url, headers, json, timeout):
        fake_post.sent = {"url": url, "headers": headers, "json": json}
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))
    return post


def test_score_call_success_and_failure(monkeypatch):
    payload = json.loads(FIXTURE.read_text())

    monkeypatch.setattr(gemini_scoring.httpx, "post", fake_post(200, gemini_body(VALID)))
    score = score_call(payload, SCENARIO, "fail", "key", "gemini-test")
    assert score["rating"] == "fail" and score["model"] == "gemini-test"
    assert fake_post.sent["url"].endswith("/models/gemini-test:generateContent")
    assert fake_post.sent["headers"] == {"x-goog-api-key": "key"}

    monkeypatch.setattr(gemini_scoring.time, "sleep", lambda secs: None)
    monkeypatch.setattr(gemini_scoring.httpx, "post", fake_post(500, {}))
    assert score_call(payload, SCENARIO, "fail", "key", "gemini-test") is None


def test_score_call_retries_busy_responses(monkeypatch):
    payload = json.loads(FIXTURE.read_text())
    monkeypatch.setattr(gemini_scoring.time, "sleep", lambda secs: None)
    responses = iter([(503, {}), (429, {}), (200, gemini_body(VALID))])

    def post(url, headers, json, timeout):
        status, body = next(responses)
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(gemini_scoring.httpx, "post", post)
    assert score_call(payload, SCENARIO, "fail", "key", "m")["rating"] == "fail"


def test_score_call_does_not_retry_bad_requests(monkeypatch):
    calls = []
    monkeypatch.setattr(gemini_scoring.time, "sleep", lambda secs: None)

    def post(url, headers, json, timeout):
        calls.append(url)
        return httpx.Response(400, json={}, request=httpx.Request("POST", url))

    monkeypatch.setattr(gemini_scoring.httpx, "post", post)
    assert score_call(json.loads(FIXTURE.read_text()), SCENARIO, "fail", "key", "m") is None
    assert len(calls) == 1


def test_webhook_scores_in_background_and_updates_call_and_dashboard(client, mongo, monkeypatch):
    monkeypatch.setattr(deps.settings, "gemini_api_key", "key")
    monkeypatch.setattr(gemini_scoring.httpx, "post", fake_post(200, gemini_body(VALID)))
    call_id = mongo.insert_call({"scenario_name": "benefits_imposter", "status": "started",
                                 "outcome": None, "flags": None, "score": None})
    payload = json.loads(FIXTURE.read_text())
    payload["data"]["conversation_initiation_client_data"]["dynamic_variables"]["call_id"] = call_id

    assert client.post("/webhooks/post-call", json=payload).status_code == 200

    stored = mongo.get_conversation("conv_test_1")
    assert stored["score"] == "fail" and stored["gemini"]["disclosed"] == ["ssn"]
    assert mongo.db["calls"].find_one()["score"] == "fail"

    recap = client.get(f"/calls/{call_id}").json()
    assert recap["score"] == "fail" and recap["disclosed"] == ["ssn"]
    assert recap["score_reason"].startswith("You started reading")

    detail = client.get("/analytics/conversations/conv_test_1").json()
    assert detail["gemini"]["reason"].startswith("You started reading")
    assert client.get("/analytics/risk").json()["disclosed"] == [{"disclosed": "ssn", "calls": 1}]


def test_safe_word_calls_are_not_scored(client, mongo, monkeypatch):
    monkeypatch.setattr(deps.settings, "gemini_api_key", "key")
    sent = []
    monkeypatch.setattr(gemini_scoring.httpx, "post", lambda *a, **k: sent.append(a))
    payload = json.loads(FIXTURE.read_text())
    tool_turn = payload["data"]["transcript"][6]["tool_calls"][0]
    tool_turn["params_as_json"] = json.dumps({"result": "stopped", "turn": 2, "flags": ""})

    client.post("/webhooks/post-call", json=payload)
    assert sent == []
    assert mongo.get_conversation("conv_test_1")["score"] is None
