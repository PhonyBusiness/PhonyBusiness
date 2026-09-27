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
        .find(
            {"outcome.result": {"$exists": True, "$ne": None}},
            {"_id": 0, "conversation_id": 1, "scenario_name": 1, "difficulty": 1,
             "started_at": 1, "duration_secs": 1, "outcome": 1},
        )
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
            "result": row["outcome"]["result"],
            "flags": row["outcome"].get("flags") or [],
        }
        for row in cursor
    ]


RESULTS = ("pass", "fail", "stopped")
FRUSTRATION_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]


def count_result(result: str) -> dict:
    return {"$sum": {"$cond": [{"$eq": ["$outcome.result", result]}, 1, 0]}}


def outcome_counts() -> dict:
    return {"calls": {"$sum": 1}, **{result: count_result(result) for result in RESULTS}}


def rate(part: int, whole: int) -> float | None:
    return round(part / whole, 3) if whole else None


def rounded(value: float | None, digits: int = 1) -> float | None:
    return round(value, digits) if value is not None else None


def with_rates(row: dict) -> dict:
    """Pass rate counts only calls the resident decided (pass or fail); stops are reported separately."""
    decided = row["pass"] + row["fail"]
    return {
        "calls": row["calls"],
        "pass": row["pass"],
        "fail": row["fail"],
        "stopped": row["stopped"],
        "pass_rate": rate(row["pass"], decided),
        "fail_rate": rate(row["fail"], decided),
        "stop_rate": rate(row["stopped"], row["calls"]),
    }


def suppress(row: dict, key: dict, min_group_size: int) -> dict:
    """Hide breakdowns too small to report without singling out a resident."""
    if row["calls"] < min_group_size:
        return {**key, "suppressed": True}
    return {**key, "suppressed": False, **with_rates(row)}


def overview(db) -> dict:
    """Overview tab: headline counts and averages across every conversation."""
    rows = list(db["conversations"].aggregate([
        {"$group": {
            "_id": None,
            **outcome_counts(),
            "avg_duration_secs": {"$avg": "$duration_secs"},
            "avg_decision_secs": {"$avg": "$outcome.decided_at_secs"},
            "avg_decision_turn": {"$avg": "$outcome.turn"},
            "total_cost_usd": {"$sum": "$cost.usd"},
            "first_call_at": {"$min": "$started_at"},
            "last_call_at": {"$max": "$started_at"},
        }},
    ]))
    if not rows or not rows[0]["calls"]:
        return {"calls": 0}
    row = rows[0]
    return {
        **with_rates(row),
        "avg_duration_secs": rounded(row["avg_duration_secs"]),
        "avg_decision_secs": rounded(row["avg_decision_secs"]),
        "avg_decision_turn": rounded(row["avg_decision_turn"]),
        "avg_cost_usd": rate(row["total_cost_usd"], row["calls"]),
        "first_call_at": row["first_call_at"],
        "last_call_at": row["last_call_at"],
    }


def trends(db, since) -> list[dict]:
    """Trends tab: one point per day for calls, pass rate, decision speed, and frustration."""
    rows = db["conversations"].aggregate([
        {"$match": {"started_at": {"$gte": since}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$started_at"}},
            **outcome_counts(),
            "avg_decision_secs": {"$avg": "$outcome.decided_at_secs"},
            "avg_peak_frustration": {"$avg": "$sentiment.peak_frustration"},
        }},
        {"$sort": {"_id": 1}},
    ])
    return [
        {
            "date": row["_id"],
            **with_rates(row),
            "avg_decision_secs": rounded(row["avg_decision_secs"]),
            "avg_peak_frustration": rounded(row["avg_peak_frustration"], 2),
        }
        for row in rows
    ]


def risk(db, min_group_size: int) -> dict:
    """Risk tab: which scams, difficulty levels, and tactics residents fall for."""
    conversations = db["conversations"]

    by_scenario = [
        suppress(row, scenario_label(row["_id"]), min_group_size)
        for row in conversations.aggregate([
            {"$group": {"_id": "$scenario_name", **outcome_counts()}},
        ])
    ]
    by_scenario.sort(key=lambda row: (row["suppressed"], -(row.get("fail_rate") or 0)))

    by_difficulty = [
        suppress(row, {"difficulty": row["_id"]}, min_group_size)
        for row in conversations.aggregate([
            {"$group": {"_id": "$difficulty", **outcome_counts()}},
            {"$sort": {"_id": 1}},
        ])
    ]

    red_flags = [
        {"flag": row["_id"], "calls": row["calls"], "on_fail": row["fail"], "on_pass": row["pass"]}
        for row in conversations.aggregate([
            {"$unwind": "$outcome.flags"},
            {"$group": {"_id": "$outcome.flags", **outcome_counts()}},
            {"$sort": {"fail": -1, "calls": -1}},
        ])
    ]

    return {
        "min_group_size": min_group_size,
        "by_scenario": by_scenario,
        "by_difficulty": by_difficulty,
        "red_flags": red_flags,
    }


def wellbeing(db) -> dict:
    """Wellbeing tab: safe-word stops, how much pressure residents felt, how calls ended."""
    conversations = db["conversations"]
    # Mongo field names can't contain dots, so buckets are keyed b0..b4 and labeled after.
    buckets = {
        f"b{index}": {"$sum": {"$cond": [{"$and": [
            {"$gte": ["$sentiment.peak_frustration", low]},
            {"$lt": ["$sentiment.peak_frustration", high]},
        ]}, 1, 0]}}
        for index, (low, high) in enumerate(FRUSTRATION_BUCKETS)
    }
    rows = list(conversations.aggregate([
        {"$group": {
            "_id": None,
            "calls": {"$sum": 1},
            "stopped": count_result("stopped"),
            "avg_peak_frustration": {"$avg": "$sentiment.peak_frustration"},
            **buckets,
        }},
    ]))
    if not rows or not rows[0]["calls"]:
        return {"calls": 0}
    row = rows[0]

    def counts_by(field: str) -> list[dict]:
        return [
            {"value": group["_id"], "calls": group["calls"]}
            for group in conversations.aggregate([
                {"$group": {"_id": f"${field}", "calls": {"$sum": 1}}},
                {"$sort": {"calls": -1}},
            ])
        ]

    return {
        "calls": row["calls"],
        "stopped": row["stopped"],
        "stop_rate": rate(row["stopped"], row["calls"]),
        "avg_peak_frustration": rounded(row["avg_peak_frustration"], 2),
        "peak_frustration_distribution": [
            {"range": f"{low:.1f}-{min(high, 1.0):.1f}", "calls": row[f"b{index}"]}
            for index, (low, high) in enumerate(FRUSTRATION_BUCKETS)
        ],
        "sentiment_labels": counts_by("sentiment.label"),
        "termination_reasons": counts_by("termination_reason"),
    }


def operations(db) -> dict:
    """Operations tab: cost per call, voice minutes, and agent response latency."""
    rows = list(db["conversations"].aggregate([
        {"$group": {
            "_id": None,
            "calls": {"$sum": 1},
            "total_cost_usd": {"$sum": "$cost.usd"},
            "avg_cost_usd": {"$avg": "$cost.usd"},
            "avg_llm_cost_usd": {"$avg": "$cost.llm_usd"},
            "total_credits": {"$sum": "$cost.credits"},
            "avg_duration_secs": {"$avg": "$duration_secs"},
            "total_agent_audio_secs": {"$sum": "$usage.agent_audio_secs"},
            "avg_llm_ttfb_secs": {"$avg": "$latency.llm_ttfb_avg_secs"},
            "max_llm_ttfb_secs": {"$max": "$latency.llm_ttfb_max_secs"},
            "calls_with_fallback": {"$sum": {"$cond": [{"$gt": ["$latency.fallback_turns", 0]}, 1, 0]}},
        }},
    ]))
    if not rows or not rows[0]["calls"]:
        return {"calls": 0}
    row = rows[0]
    return {
        "calls": row["calls"],
        "total_cost_usd": rounded(row["total_cost_usd"], 2),
        "avg_cost_usd": rounded(row["avg_cost_usd"], 3),
        "avg_llm_cost_usd": rounded(row["avg_llm_cost_usd"], 4),
        "total_credits": row["total_credits"],
        "avg_duration_secs": rounded(row["avg_duration_secs"]),
        "total_agent_audio_mins": rounded(row["total_agent_audio_secs"] / 60),
        "avg_llm_ttfb_secs": rounded(row["avg_llm_ttfb_secs"], 2),
        "max_llm_ttfb_secs": rounded(row["max_llm_ttfb_secs"], 2),
        "fallback_rate": rate(row["calls_with_fallback"], row["calls"]),
    }
