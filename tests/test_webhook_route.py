"""POST /webhooks/post-call stores the conversation and closes the matching call."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from backend import main

FIXTURE = Path(__file__).parent / "fixtures" / "post_call_webhook.json"


def payload_for(call_id: str | None = None) -> dict:
    payload = json.loads(FIXTURE.read_text())
    if call_id:
        payload["data"]["conversation_initiation_client_data"]["dynamic_variables"]["call_id"] = call_id
    return payload


def insert_call(mongo, **fields) -> str:
    now = datetime.now(timezone.utc)
    document = {"scenario_name": "tech_support", "dynamic_variables": {"difficulty": "hard"},
                "status": "started", "outcome": None, "flags": None, "created_at": now, "updated_at": now}
    return mongo.insert_call(document | fields)


def test_stores_conversation_and_links_call(client, mongo):
    call_id = insert_call(mongo)
    response = client.post("/webhooks/post-call", json=payload_for(call_id))

    assert response.json() == {"status": "stored", "conversation_id": "conv_test_1"}
    stored = mongo.get_conversation("conv_test_1")
    assert stored["call_id"] == call_id
    # Scenario and difficulty come from the webhook, not the call record.
    assert stored["scenario_name"] == "benefits_imposter"
    assert stored["difficulty"] == "2"

    call = mongo.db["calls"].find_one()
    assert call["status"] == "ended"
    assert call["conversation_id"] == "conv_test_1"
    assert call["outcome"] == "pass"


def test_live_outcome_is_not_overwritten(client, mongo):
    call_id = insert_call(mongo, outcome="fail", flags=["Asks for secrecy"])
    client.post("/webhooks/post-call", json=payload_for(call_id))

    call = mongo.db["calls"].find_one()
    assert call["outcome"] == "fail"
    assert call["flags"] == ["Asks for secrecy"]


def test_retries_do_not_duplicate(client, mongo):
    client.post("/webhooks/post-call", json=payload_for())
    client.post("/webhooks/post-call", json=payload_for())
    assert mongo.db["conversations"].count_documents({}) == 1


def test_other_event_types_are_ignored(client, mongo):
    response = client.post("/webhooks/post-call", json={"type": "post_call_audio", "data": {}})
    assert response.json() == {"status": "ignored"}
    assert mongo.db["conversations"].count_documents({}) == 0


def test_signature_required_when_secret_is_set(client, monkeypatch):
    monkeypatch.setattr(main.settings, "elevenlabs_webhook_secret", "secret")
    body = json.dumps(payload_for()).encode()

    assert client.post("/webhooks/post-call", content=body).status_code == 401

    timestamp = int(time.time())
    digest = hmac.new(b"secret", f"{timestamp}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
    response = client.post("/webhooks/post-call", content=body,
                           headers={"ElevenLabs-Signature": f"t={timestamp},v0={digest}"})
    assert response.status_code == 200
