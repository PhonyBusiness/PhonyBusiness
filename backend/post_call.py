"""Turn the ElevenLabs post-call webhook into the conversation record we store.

We keep results, not conversations: the stored record holds timing, outcome,
sentiment, and cost, but never the transcript text, the resident's name, or
the conversation history.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from statistics import mean

from backend.scenarios import SCENARIOS

SIGNATURE_TOLERANCE_SECS = 30 * 60


def verify_signature(raw_body: bytes, header: str | None, secret: str, now: float | None = None) -> bool:
    """Check the ElevenLabs-Signature header ("t=<unix>,v0=<hex hmac>") against the raw body."""
    if not header:
        return False
    try:
        parts = dict(part.split("=", 1) for part in header.split(","))
        timestamp = parts["t"]
        signature = parts["v0"]
        issued_at = int(timestamp)
    except (KeyError, ValueError):
        return False

    now = time.time() if now is None else now
    if abs(now - issued_at) > SIGNATURE_TOLERANCE_SECS:
        return False

    expected = hmac.new(
        secret.encode(), f"{timestamp}.{raw_body.decode()}".encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def split_flags(value: str | list[str] | None) -> list[str]:
    """The agent may send flags as a list or as one comma-separated string."""
    if not value:
        return []
    if isinstance(value, str):
        return [flag.strip() for flag in value.split(",") if flag.strip()]
    return [str(flag).strip() for flag in value if str(flag).strip()]


def dynamic_variables(data: dict) -> dict:
    client_data = data.get("conversation_initiation_client_data") or {}
    return client_data.get("dynamic_variables") or {}


def find_outcome(transcript: list[dict]) -> dict | None:
    """Return the last record_outcome tool call the agent made, if any."""
    outcome = None
    for turn in transcript:
        for call in turn.get("tool_calls") or []:
            if call.get("tool_name") != "record_outcome":
                continue
            try:
                params = json.loads(call.get("params_as_json") or "{}")
            except json.JSONDecodeError:
                params = {}
            outcome = {
                "result": str(params.get("result", "")).strip().lower() or None,
                "flags": split_flags(params.get("flags")),
                "turn": params.get("turn"),
                "decided_at_secs": turn.get("time_in_call_secs"),
            }
    return outcome


def scenario_for_persona(persona: str | None) -> str | None:
    for scenario in SCENARIOS:
        if scenario["persona"] == persona:
            return scenario["name"]
    return None


def summarize_latency(transcript: list[dict]) -> dict:
    ttfbs = []
    fallback_turns = 0
    for turn in transcript:
        if turn.get("role") != "agent":
            continue
        if turn.get("llm_override"):
            fallback_turns += 1
        metrics = (turn.get("conversation_turn_metrics") or {}).get("metrics") or {}
        ttfb = (metrics.get("convai_llm_service_ttfb") or {}).get("elapsed_time")
        if ttfb is not None:
            ttfbs.append(ttfb)
    return {
        "llm_ttfb_avg_secs": round(mean(ttfbs), 3) if ttfbs else None,
        "llm_ttfb_max_secs": round(max(ttfbs), 3) if ttfbs else None,
        "fallback_turns": fallback_turns,
    }


def summarize_models(charging: dict) -> dict:
    usage = ((charging.get("llm_usage") or {}).get("irreversible_generation") or {}).get("model_usage") or {}
    return {
        model: {
            "input_tokens": (tokens.get("input") or {}).get("tokens", 0),
            "output_tokens": (tokens.get("output_total") or {}).get("tokens", 0),
        }
        for model, tokens in usage.items()
    }


def build_conversation(payload: dict, call: dict | None = None) -> dict:
    """Build the stored conversation document from a post_call_transcription payload."""
    data = payload.get("data") or {}
    metadata = data.get("metadata") or {}
    analysis = data.get("analysis") or {}
    sentiment = analysis.get("sentiment_analysis") or {}
    charging = metadata.get("charging") or {}
    transcript = data.get("transcript") or []
    variables = dynamic_variables(data)

    started = metadata.get("start_time_unix_secs")
    duration = metadata.get("call_duration_secs")
    started_at = datetime.fromtimestamp(started, tz=timezone.utc) if started else None

    timeline = []
    for turn in transcript:
        if turn.get("role") not in ("agent", "user") or turn.get("message") is None:
            continue
        point = {"t": turn.get("time_in_call_secs"), "role": turn["role"], "interrupted": bool(turn.get("interrupted"))}
        scores = turn.get("analysis") or {}
        if "user_sentiment_score" in scores:
            point["sentiment"] = scores["user_sentiment_score"]
            point["frustration"] = scores.get("user_frustration_score")
        timeline.append(point)

    call = call or {}
    call_variables = call.get("dynamic_variables") or {}

    return {
        "conversation_id": data.get("conversation_id"),
        "call_id": str(call["_id"]) if call.get("_id") else variables.get("call_id"),
        "agent_id": data.get("agent_id"),
        "scenario_name": call.get("scenario_name") or scenario_for_persona(variables.get("persona")),
        "difficulty": str(call_variables.get("difficulty") or variables.get("difficulty") or "") or None,
        "status": data.get("status"),
        "started_at": started_at,
        "duration_secs": duration,
        "termination_reason": metadata.get("termination_reason"),
        "outcome": find_outcome(transcript),
        "turns": {
            "agent": sum(1 for point in timeline if point["role"] == "agent"),
            "user": sum(1 for point in timeline if point["role"] == "user"),
        },
        "timeline": timeline,
        "sentiment": {
            "label": sentiment.get("overall_label"),
            "score": sentiment.get("overall_sentiment_score"),
            "peak_frustration": sentiment.get("max_user_frustration_score"),
            "min_sentiment": sentiment.get("min_user_sentiment_score"),
        },
        "call_successful": analysis.get("call_successful"),
        "latency": summarize_latency(transcript),
        "cost": {
            "usd": metadata.get("cost_fiat"),
            "credits": metadata.get("cost"),
            "llm_usd": charging.get("llm_price"),
        },
        "usage": {
            "agent_audio_secs": (charging.get("tts_usage") or {}).get("total_audio_output_seconds"),
            "user_audio_secs": (charging.get("asr_usage") or {}).get("total_audio_input_seconds"),
            "models": summarize_models(charging),
        },
        "language": metadata.get("main_language"),
        "source": metadata.get("conversation_initiation_source"),
        "score": None,
        "received_at": datetime.now(timezone.utc),
    }
