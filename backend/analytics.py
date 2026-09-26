"""Read-side analytics over the stored conversations, one function per dashboard view.

Every function returns plain JSON-ready dicts. Nothing here reads names or
transcript text, because neither is stored.
"""

from backend.scenarios import get_scenario
from backend.tips import get_tips


def scenario_label(name: str | None) -> dict:
    scenario = get_scenario(name) if name else None
    return {"name": name, "display_name": scenario["display_name"] if scenario else None}


def conversation_detail(conversation: dict) -> dict:
    """Per-conversation analytics for one call, built from its stored record."""
    outcome = conversation.get("outcome") or {}
    duration = conversation.get("duration_secs")
    decided_at = outcome.get("decided_at_secs")
    flags = outcome.get("flags") or []

    return {
        "conversation_id": conversation["conversation_id"],
        "call_id": conversation.get("call_id"),
        "scenario": scenario_label(conversation.get("scenario_name")),
        "difficulty": conversation.get("difficulty"),
        "started_at": conversation.get("started_at"),
        "duration_secs": duration,
        "termination_reason": conversation.get("termination_reason"),
        "outcome": {
            "result": outcome.get("result"),
            "flags": flags,
            "turn": outcome.get("turn"),
            "decided_at_secs": decided_at,
            "decided_at_share": round(decided_at / duration, 2) if decided_at and duration else None,
        },
        "tips": [{"flag": tip["label"], "do": tip["do"], "dont": tip["dont"]} for tip in get_tips(flags)],
        "turns": conversation.get("turns"),
        "frustration_timeline": [
            {"t": point["t"], "sentiment": point.get("sentiment"), "frustration": point.get("frustration")}
            for point in conversation.get("timeline") or []
            if "frustration" in point
        ],
        "sentiment": conversation.get("sentiment"),
        "call_successful": conversation.get("call_successful"),
        "score": conversation.get("score"),
        "latency": conversation.get("latency"),
        "cost": conversation.get("cost"),
    }


def recent_conversations(db, limit: int) -> list[dict]:
    """Feed rows for the dashboard: scenario, outcome, flags, and time only."""
    cursor = (
        db["conversations"]
        .find({}, {"_id": 0, "conversation_id": 1, "scenario_name": 1, "difficulty": 1,
                   "started_at": 1, "duration_secs": 1, "outcome": 1})
        .sort("started_at", -1)
        .limit(limit)
    )
    return [
        {
            "conversation_id": row["conversation_id"],
            "scenario": scenario_label(row.get("scenario_name")),
            "difficulty": row.get("difficulty"),
            "started_at": row.get("started_at"),
            "duration_secs": row.get("duration_secs"),
            "result": (row.get("outcome") or {}).get("result"),
            "flags": (row.get("outcome") or {}).get("flags") or [],
        }
        for row in cursor
    ]
