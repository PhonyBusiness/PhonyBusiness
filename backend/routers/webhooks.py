"""Routes ElevenLabs calls after a conversation ends."""

import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from backend.deps import mongo, settings
from backend.gemini_scoring import score_call
from backend.post_call import build_conversation, dynamic_variables, verify_signature
from backend.scenarios import get_scenario

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhooks/post-call")
async def post_call_webhook(request: Request, background: BackgroundTasks) -> dict[str, str]:
    """Store the analytics fields of a finished conversation; the transcript text is never saved."""
    raw_body = await request.body()
    if settings.elevenlabs_webhook_secret:
        if not verify_signature(raw_body, request.headers.get("ElevenLabs-Signature"), settings.elevenlabs_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    else:
        logger.warning("ELEVENLABS_WEBHOOK_SECRET is not set; accepting unsigned post-call webhook")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body is not JSON") from exc

    if payload.get("type") != "post_call_transcription":
        return {"status": "ignored"}

    data = payload.get("data") or {}
    conversation_id = data.get("conversation_id")
    if not conversation_id:
        raise HTTPException(status_code=400, detail="Missing conversation_id")

    # Dashboard data comes from the webhook alone; the call record is only marked ended.
    conversation = build_conversation(payload)
    mongo.save_conversation(conversation)
    call = mongo.find_call_for_conversation(conversation_id, dynamic_variables(data).get("call_id"))
    if call is not None:
        mongo.close_call_from_webhook(call["_id"], conversation)

    # Scoring waits on Gemini, so it runs after we've answered ElevenLabs.
    background.add_task(score_and_save, payload, conversation)
    return {"status": "stored", "conversation_id": conversation_id}


def score_and_save(payload: dict, conversation: dict) -> None:
    scenario = get_scenario(conversation["scenario_name"]) if conversation.get("scenario_name") else None
    recorded = (conversation.get("outcome") or {}).get("result")
    if recorded == "stopped":
        return  # The safe word ends the call with no judgment, so it isn't scored.
    score = score_call(payload, scenario, recorded, settings.gemini_api_key, settings.gemini_model)
    if score is not None:
        mongo.save_score(conversation["conversation_id"], conversation.get("call_id"), score)
