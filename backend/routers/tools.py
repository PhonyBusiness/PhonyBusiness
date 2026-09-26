"""Routes ElevenLabs calls live, mid-conversation, as agent server tools."""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator

from backend.deps import mongo
from backend.tips import get_tips

router = APIRouter()


class RecordOutcomeRequest(BaseModel):
    call_id: str
    result: str
    flags: list[str]
    turn: int

    @field_validator("flags", mode="before")
    @classmethod
    def split_comma_separated_flags(cls, value: str | list[str]) -> list[str]:
        """The agent only ever saw red_flags as one joined string, so it may echo
        that format back instead of a JSON array."""
        if isinstance(value, str):
            return [flag.strip() for flag in value.split(",") if flag.strip()]
        return value


@router.post("/tools/record_outcome", response_class=PlainTextResponse)
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
