"""Per-conversation analytics and the recent calls feed."""

import json
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "post_call_webhook.json"


def store(client, conversation_id="conv_test_1", start=1790450350):
    payload = json.loads(FIXTURE.read_text())
    payload["data"]["conversation_id"] = conversation_id
    payload["data"]["metadata"]["start_time_unix_secs"] = start
    client.post("/webhooks/post-call", json=payload)


def test_conversation_detail(client):
    store(client)
    body = client.get("/analytics/conversations/conv_test_1").json()

    assert body["scenario"] == {"name": "benefits_imposter", "display_name": "Benefits imposter"}
    assert body["outcome"]["result"] == "pass"
    assert body["outcome"]["decided_at_secs"] == 91
    assert body["outcome"]["decided_at_share"] == 0.67
    assert [tip["flag"] for tip in body["tips"]] == [
        "Urgency or threat of losing benefits", "Requests a Social Security number"]
    assert [point["frustration"] for point in body["frustration_timeline"]] == [0.0, 0.3]
    assert "timeline" not in body and "usage" not in body


def test_unknown_conversation_is_404(client):
    assert client.get("/analytics/conversations/nope").status_code == 404


def test_recent_feed_is_newest_first_and_minimal(client):
    store(client, "conv_old", start=1790000000)
    store(client, "conv_new", start=1790450350)
    rows = client.get("/analytics/conversations?limit=5").json()

    assert [row["conversation_id"] for row in rows] == ["conv_new", "conv_old"]
    assert set(rows[0]) == {"conversation_id", "scenario", "difficulty", "started_at",
                            "duration_secs", "result", "flags"}
