"""Seed the conversations collection with demo data for the dashboard.

Loads the real sample post-call webhook we received, plus generated calls
built in the same webhook shape, all run through build_conversation so the
stored documents match what real webhooks produce. Every seeded document is
tagged demo_seed=True.

    uv run python scripts/seed_demo_data.py            # add 120 demo calls plus the real sample
    uv run python scripts/seed_demo_data.py --count 100 --days 21
    uv run python scripts/seed_demo_data.py --clear    # remove all demo calls
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import get_settings  # noqa: E402
from backend.database import MongoDatabase  # noqa: E402
from backend.post_call import build_conversation  # noqa: E402
from backend.scenarios import SCENARIOS  # noqa: E402

MVP_SCENARIOS = {"benefits_imposter", "tech_support", "family_emergency"}
BASE_FAIL_RATE = {"easy": 0.15, "medium": 0.35, "hard": 0.6}
STOP_RATE = 0.05
COST_PER_SEC = 0.092 / 136
CREDITS_PER_SEC = 925 / 136


def user_turn(t: int, sentiment: float, frustration: float) -> dict:
    return {"role": "user", "message": "", "time_in_call_secs": t,
            "analysis": {"user_sentiment_score": sentiment, "user_frustration_score": frustration}}


def agent_turn(t: int, ttfb: float, fallback: bool = False) -> dict:
    turn = {"role": "agent", "message": "", "time_in_call_secs": t,
            "conversation_turn_metrics": {"metrics": {"convai_llm_service_ttfb": {"elapsed_time": ttfb}}}}
    if fallback:
        turn["llm_override"] = "gemini-2.5-flash"
    return turn


def tool_turn(t: int, result: str, turn: int, flags: list[str] | str) -> dict:
    params = {"result": result, "turn": turn, "flags": flags}
    return {"role": "agent", "message": None, "time_in_call_secs": t,
            "tool_calls": [{"tool_name": "record_outcome", "params_as_json": json.dumps(params)}]}


def webhook(conversation_id: str, start: int, duration: int, persona: str, difficulty: str,
            transcript: list[dict], sentiment: dict, termination: str, models: dict) -> dict:
    return {
        "type": "post_call_transcription",
        "data": {
            "agent_id": "agent_4301m3ecd2acfz4a2qpqvqjsv9sw",
            "status": "done",
            "conversation_id": conversation_id,
            "metadata": {
                "start_time_unix_secs": start,
                "call_duration_secs": duration,
                "cost": round(duration * CREDITS_PER_SEC),
                "cost_fiat": duration * COST_PER_SEC,
                "termination_reason": termination,
                "main_language": "en",
                "conversation_initiation_source": "react_sdk",
                "charging": {
                    "llm_price": duration * 0.000127,
                    "llm_usage": {"irreversible_generation": {"model_usage": models}},
                    "tts_usage": {"total_audio_output_seconds": round(duration * 0.64, 1)},
                    "asr_usage": {"total_audio_input_seconds": round(duration * 0.28, 1)},
                },
            },
            "analysis": {"call_successful": "success", "sentiment_analysis": sentiment},
            "conversation_initiation_client_data": {
                "dynamic_variables": {"persona": persona, "difficulty": difficulty},
            },
            "transcript": transcript,
        },
    }


def real_sample() -> dict:
    """The sample benefits-imposter call from Sep 26, 2026, reduced to the fields we store."""
    return webhook(
        conversation_id="conv_3001m3fjgep3e1n9j13ks6w317r9",
        start=1790450350,
        duration=136,
        persona="Officer Daniels from the Federal Benefits Office",
        difficulty="2",
        transcript=[
            agent_turn(0, 0.0), user_turn(9, 0.0, 0.0), agent_turn(12, 1.214),
            user_turn(25, 0.0, 0.0), agent_turn(28, 1.036), user_turn(41, 0.0, 0.1),
            agent_turn(44, 1.465), user_turn(55, -0.2, 0.3), agent_turn(70, 4.993, fallback=True),
            user_turn(85, -0.1, 0.2),
            tool_turn(91, "pass", 5, "urgency,threat of losing benefits,asking to verify ID over the phone"),
            agent_turn(93, 1.644), user_turn(128, 0.0, 0.0), agent_turn(131, 1.687),
        ],
        sentiment={"overall_label": "neutral", "overall_sentiment_score": 0.0,
                   "max_user_frustration_score": 0.3, "min_user_sentiment_score": -0.2},
        termination="end_call tool was called.",
        models={"gemini-3.8-flash": {"input": {"tokens": 14603}, "output_total": {"tokens": 347}},
                "gemini-2.5-flash": {"input": {"tokens": 2217}, "output_total": {"tokens": 112}}},
    )


def generated_call(rng: random.Random, index: int, now: datetime, days: int) -> dict:
    scenario = rng.choices(SCENARIOS, weights=[3 if s["name"] in MVP_SCENARIOS else 1 for s in SCENARIOS])[0]
    difficulty = rng.choice(list(BASE_FAIL_RATE))
    days_ago = rng.uniform(0, days)
    started = now - timedelta(days=days_ago, hours=rng.uniform(0, 8))

    # Older calls fail more often, so the Trends tab shows residents improving.
    fail_rate = BASE_FAIL_RATE[difficulty] * (0.6 + 0.6 * days_ago / days)
    roll = rng.random()
    result = "stopped" if roll < STOP_RATE else "fail" if roll < STOP_RATE + fail_rate else "pass"

    user_turns = rng.randint(3, 7)
    decided_turn = rng.randint(2, user_turns)
    transcript, t, frustration, fallback_used = [agent_turn(0, 0.0)], 0, 0.0, False
    for turn in range(1, user_turns + 1):
        t += rng.randint(8, 16)
        rise = 0.3 if result != "pass" else 0.12
        frustration = min(1.0, max(0.0, frustration + rng.uniform(-0.05, rise)))
        transcript.append(user_turn(t, round(-frustration * rng.uniform(0.5, 1.0), 2), round(frustration, 2)))
        t += rng.randint(2, 5)
        fallback = not fallback_used and rng.random() < 0.08
        fallback_used = fallback_used or fallback
        transcript.append(agent_turn(t, round(rng.uniform(4.0, 5.5) if fallback else rng.uniform(0.9, 1.8), 3), fallback))
        if turn == decided_turn:
            flags = rng.sample(scenario["red_flags"], k=rng.randint(2, 3))
            transcript.append(tool_turn(t + 1, result, turn, flags))
            break
    t += rng.randint(30, 60)  # debrief
    transcript.append(agent_turn(t, round(rng.uniform(1.2, 2.0), 3)))
    duration = t + rng.randint(2, 6)

    peak = max(point["analysis"]["user_frustration_score"] for point in transcript if point["role"] == "user")
    low = min(point["analysis"]["user_sentiment_score"] for point in transcript if point["role"] == "user")
    label = "negative" if peak >= 0.6 else "neutral"
    termination = "Client disconnected" if result == "stopped" or rng.random() < 0.1 else "end_call tool was called."
    tokens = duration * 110
    return webhook(
        conversation_id=f"demo_{index:03d}",
        start=int(started.timestamp()),
        duration=duration,
        persona=scenario["persona"],
        difficulty=difficulty,
        transcript=transcript,
        sentiment={"overall_label": label, "overall_sentiment_score": round(low / 2, 2),
                   "max_user_frustration_score": peak, "min_user_sentiment_score": low},
        termination=termination,
        models={"gemini-3.8-flash": {"input": {"tokens": tokens}, "output_total": {"tokens": tokens // 40}}},
    )


def demo_conversations(count: int, days: int, now: datetime, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    payloads = [real_sample()] + [generated_call(rng, i, now, days) for i in range(1, count + 1)]
    return [build_conversation(payload) | {"demo_seed": True} for payload in payloads]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=120, help="generated calls in addition to the real sample")
    parser.add_argument("--days", type=int, default=14, help="spread generated calls over this many past days")
    parser.add_argument("--clear", action="store_true", help="delete every demo_seed document and exit")
    args = parser.parse_args()

    mongo = MongoDatabase(get_settings().mongodb_uri)
    mongo.connect()
    try:
        conversations = mongo.db["conversations"]
        if args.clear:
            print(f"Deleted {conversations.delete_many({'demo_seed': True}).deleted_count} demo conversations")
            return
        seeded = demo_conversations(args.count, args.days, datetime.now(timezone.utc))
        for conversation in seeded:
            mongo.save_conversation(conversation)
        print(f"Seeded {len(seeded)} demo conversations into {mongo.db.name}.conversations")
    finally:
        mongo.close()


if __name__ == "__main__":
    main()
