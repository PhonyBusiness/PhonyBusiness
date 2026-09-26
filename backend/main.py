"""FastAPI entry point for PhonyBusiness."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator

from backend.config import get_settings
from backend.database import MongoDatabase
from backend.elevenlabs_client import ElevenLabsError, get_signed_url
from backend.scenarios import get_scenario, list_scenarios
from backend.tips import get_tips


settings = get_settings()
mongo = MongoDatabase(settings.mongodb_uri)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open and verify external connections when the API process starts."""
    mongo.connect()
    app.state.mongo = mongo
    try:
        yield
    finally:
        mongo.close()


app = FastAPI(title="PhonyBusiness API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process and database connection are running."""
    return {
        "status": "ok",
        "mongodb": "connected" if mongo.is_connected else "disconnected",
    }


class ScenarioSummary(BaseModel):
    name: str
    display_name: str


@app.get("/scenarios", response_model=list[ScenarioSummary])
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


@app.post("/calls/start", response_model=StartCallResponse)
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
    )


class SessionRequest(BaseModel):
    conversation_id: str


@app.post("/calls/{call_id}/session")
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


@app.post("/calls/{call_id}/hangup")
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


class RecordOutcomeRequest(BaseModel):
    call_id: str
    result: str
    flags: list[str]
    turn: int

    @field_validator("flags", mode="before")
    @classmethod
    def split_comma_separated_flags(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [flag.strip() for flag in value.split(",") if flag.strip()]
        return value


@app.post("/tools/record_outcome", response_class=PlainTextResponse)
def record_outcome(payload: RecordOutcomeRequest) -> str:
    """Save the live outcome reported by the agent and return tips for it to read aloud."""
    try:
        oid = ObjectId(payload.call_id)
    except InvalidId as exc:
        raise HTTPException(status_code=400, detail="Invalid call_id") from exc

    call = mongo.record_outcome(oid, payload.result, payload.flags, payload.turn)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    tips = get_tips(payload.flags)
    return " ".join(f"{tip['label']}. Do: {tip['do']} Don't: {tip['dont']}" for tip in tips)


class TipItem(BaseModel):
    do: str
    dont: str


class CallDetailResponse(BaseModel):
    call_id: str
    status: str
    outcome: str | None
    score: str | None
    flags: list[str] | None
    tips: list[TipItem] | None


@app.get("/calls/{call_id}", response_model=CallDetailResponse)
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
        flags=flags,
        tips=tips,
    )
