"""The demo seed produces realistic, privacy-safe, removable conversations."""

import json
from datetime import datetime, timezone

from backend import analytics
from scripts.seed_demo_data import demo_conversations

NOW = datetime(2026, 9, 26, 22, 0, tzinfo=timezone.utc)


def test_seed_is_tagged_deterministic_and_includes_the_real_sample():
    first = demo_conversations(60, 14, NOW)
    assert len(first) == 61
    assert all(conversation["demo_seed"] for conversation in first)
    assert first[0]["conversation_id"] == "conv_3001m3fjgep3e1n9j13ks6w317r9"
    assert first[0]["outcome"]["decided_at_secs"] == 91
    strip = lambda rows: [{k: v for k, v in row.items() if k != "received_at"} for row in rows]  # noqa: E731
    assert strip(demo_conversations(60, 14, NOW)) == strip(first)


def test_seed_covers_every_tab(mongo):
    for conversation in demo_conversations(60, 14, NOW):
        mongo.save_conversation(conversation)
    db = mongo.db

    overview = analytics.overview(db)
    assert overview["calls"] == 61
    assert overview["pass"] and overview["fail"] and overview["stopped"]

    risk = analytics.risk(db, 5)
    assert any(not row["suppressed"] for row in risk["by_scenario"])
    assert all(not row["suppressed"] for row in risk["by_difficulty"] if row["difficulty"] != "2")

    assert len(analytics.trends(db, datetime(2026, 9, 1, tzinfo=timezone.utc))) >= 10
    assert analytics.operations(db)["fallback_rate"] > 0


def test_seed_stores_no_text():
    stored = json.dumps(demo_conversations(10, 14, NOW), default=str)
    assert '"message"' not in stored
