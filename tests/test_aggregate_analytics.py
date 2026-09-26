"""Aggregate analytics endpoints, one per dashboard tab."""

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend import deps

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "post_call_webhook.json").read_text())
TODAY = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)


def post(client, n, result, persona="Officer Daniels from the Federal Benefits Office",
         difficulty="easy", day=0, frustration=0.3, flags="Asks for secrecy", termination="end_call tool was called."):
    payload = copy.deepcopy(FIXTURE)
    data = payload["data"]
    data["conversation_id"] = f"conv_{result}_{persona[:5]}_{n}_{day}"
    data["metadata"]["start_time_unix_secs"] = int((TODAY - timedelta(days=day)).timestamp())
    data["metadata"]["termination_reason"] = termination
    data["analysis"]["sentiment_analysis"]["max_user_frustration_score"] = frustration
    variables = data["conversation_initiation_client_data"]["dynamic_variables"]
    variables["persona"] = persona
    variables["difficulty"] = difficulty
    tool_turn = data["transcript"][6]
    tool_turn["tool_calls"][0]["params_as_json"] = json.dumps({"result": result, "turn": 3, "flags": flags})
    client.post("/webhooks/post-call", json=payload)


@pytest.fixture
def seeded(client, monkeypatch):
    monkeypatch.setattr(deps.settings, "analytics_min_group_size", 5)
    for n in range(4):
        post(client, n, "pass", day=0)
    for n in range(2):
        post(client, n, "fail", day=1, frustration=0.7, flags="Requests a Social Security number, Asks for secrecy")
    post(client, 0, "stopped", day=1, frustration=0.9, termination="Client disconnected")
    # Three tech support calls: below the group size, so their breakdown is hidden.
    for n in range(3):
        post(client, n, "fail", persona="a support technician from SecureTech Support", difficulty="hard")
    return client


def test_overview(seeded):
    body = seeded.get("/analytics/overview").json()
    assert (body["calls"], body["pass"], body["fail"], body["stopped"]) == (10, 4, 5, 1)
    assert body["pass_rate"] == pytest.approx(4 / 9, abs=0.001)
    assert body["stop_rate"] == 0.1
    assert body["avg_decision_secs"] == 91.0


def test_overview_empty(client):
    assert client.get("/analytics/overview").json() == {"calls": 0}


def test_trends_groups_by_day(seeded):
    points = seeded.get("/analytics/trends?days=7").json()
    assert [(p["date"], p["calls"]) for p in points] == [
        ((TODAY - timedelta(days=1)).strftime("%Y-%m-%d"), 3),
        (TODAY.strftime("%Y-%m-%d"), 7),
    ]


def test_risk_suppresses_small_groups(seeded):
    body = seeded.get("/analytics/risk").json()
    by_name = {row["name"]: row for row in body["by_scenario"]}

    assert by_name["benefits_imposter"]["calls"] == 7
    assert by_name["benefits_imposter"]["fail_rate"] == pytest.approx(2 / 6, abs=0.001)
    assert by_name["tech_support"] == {"name": "tech_support", "display_name": "Tech support", "suppressed": True}
    assert {row["difficulty"]: row["suppressed"] for row in body["by_difficulty"]} == {"easy": False, "hard": True}

    top_flag = body["red_flags"][0]
    assert top_flag["flag"] == "Asks for secrecy"
    assert (top_flag["calls"], top_flag["on_fail"]) == (10, 5)


def test_wellbeing(seeded):
    body = seeded.get("/analytics/wellbeing").json()
    assert body["stop_rate"] == 0.1
    assert {b["range"]: b["calls"] for b in body["peak_frustration_distribution"]} == {
        "0.0-0.2": 0, "0.2-0.4": 7, "0.4-0.6": 0, "0.6-0.8": 2, "0.8-1.0": 1}
    assert body["termination_reasons"][0] == {"value": "end_call tool was called.", "calls": 9}


def test_operations(seeded):
    body = seeded.get("/analytics/operations").json()
    assert body["calls"] == 10
    assert body["avg_cost_usd"] == 0.092
    assert body["fallback_rate"] == 1.0
    assert body["max_llm_ttfb_secs"] == 5.0
