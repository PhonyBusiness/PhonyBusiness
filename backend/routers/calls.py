"""Routes the browser calls directly: scenario listing and call lifecycle."""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.deps import mongo, settings
from backend.elevenlabs_client import ElevenLabsError, get_signed_url
from backend.scenarios import get_scenario, list_scenarios
from backend.tips import get_tips
from backend.voices import get_voice_id

router = APIRouter()


class ScenarioSummary(BaseModel):
    name: str
    display_name: str


@router.get("/scenarios", response_model=list[ScenarioSummary])
def scenarios() -> list[dict]:
    """List scenarios for the start screen's dropdown (names only, no spoilers)."""
    return list_scenarios()


class StartCallRequest(BaseModel):
    first_name: str
    scenario: str
    difficulty: str

class StartCallResponse(BaseModel):
    call_id: str
    caller_name: str
    signed_url: str
    dynamic_variables: dict[str, str]
    voice_id: str | None = None

@router.post("/calls/start", response_model=StartCallResponse)
def start_call(payload: StartCallRequest) -> StartCallResponse:
    """Look up the chosen scenario, create a call record, and hand back a signed ElevenLabs session."""
    scenario = get_scenario(payload.scenario)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Unknown scenario")

    dynamic_variables = {
        "first_name": payload.first_name,
        "persona": scenario["persona"],
        "ask": scenario["ask"],
        "red_flags": ", ".join(scenario["red_flags"]),
        "difficulty": payload.difficulty,
        "safe_word": settings.safe_word,
    }

    now = datetime.now(timezone.utc)
    call_id = mongo.insert_call(
        {
            "scenario_name": scenario["name"],
            "first_name": payload.first_name,
            "dynamic_variables": dynamic_variables,
            "red_flags": scenario["red_flags"],
            "conversation_id": None,
            "status": "started",
            "outcome": None,
            "flags": None,
            "score": None,
            "created_at": now,
            "updated_at": now,
        }
    )

    try:
        signed_url = get_signed_url(settings.elevenlabs_agent_id, settings.elevenlabs_api_key)
    except ElevenLabsError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Added after the Mongo insert so the stored snapshot doesn't duplicate the doc's own _id.
    dynamic_variables["call_id"] = call_id

    return StartCallResponse(
        call_id=call_id,
        caller_name=scenario["caller_display_name"],
        signed_url=signed_url,
        dynamic_variables=dynamic_variables,
        voice_id=get_voice_id(scenario["name"]),
    )


class SessionRequest(BaseModel):
    conversation_id: str


@router.post("/calls/{call_id}/session")
def set_call_session(call_id: str, payload: SessionRequest) -> dict[str, str]:
    """Record the ElevenLabs conversation_id so the post-call webhook can match it later."""
    try:
        oid = ObjectId(call_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid call_id") from exc

    found = mongo.set_conversation_id(oid, payload.conversation_id)
    if not found:
        raise HTTPException(status_code=404, detail="Call not found")

    return {"status": "ok"}


@router.post("/calls/{call_id}/hangup")
def hangup_call(call_id: str) -> dict[str, str | None]:
    """End the call; if no outcome was recorded yet, hanging up counts as a pass."""
    try:
        oid = ObjectId(call_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid call_id") from exc

    call = mongo.hangup_call(oid)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    return {"call_id": call_id, "status": call["status"], "outcome": call["outcome"]}


class TipItem(BaseModel):
    do: str
    dont: str


class CallDetailResponse(BaseModel):
    call_id: str
    status: str
    outcome: str | None
    score: str | None
    score_reason: str | None = None
    disclosed: list[str] | None = None
    flags: list[str] | None
    tips: list[TipItem] | None


@router.get("/calls/{call_id}", response_model=CallDetailResponse)
def get_call(call_id: str) -> CallDetailResponse:
    """Recap screen data. Never exposes the transcript, dynamic_variables, or first_name."""
    try:
        oid = ObjectId(call_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid call_id") from exc

    call = mongo.get_call(oid)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    flags = call.get("flags")
    ended = call["status"] == "ended"
    tips = [{"do": tip["do"], "dont": tip["dont"]} for tip in get_tips(flags)] if ended else None

    return CallDetailResponse(
        call_id=call_id,
        status=call["status"],
        outcome=call.get("outcome"),
        score=call.get("score"),
        score_reason=call.get("score_reason"),
        disclosed=call.get("disclosed"),
        flags=flags,
        tips=tips,
    )
