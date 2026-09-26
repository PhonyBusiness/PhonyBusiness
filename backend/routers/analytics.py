"""Routes the dashboard calls: per-conversation analytics and one endpoint per tab."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from backend import analytics
from backend.deps import mongo, settings

router = APIRouter(prefix="/analytics")


@router.get("/conversations")
def list_conversations(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
    """Recent calls feed: scenario, outcome, flags, and time. No names or transcripts."""
    return analytics.recent_conversations(mongo.db, limit)


@router.get("/conversations/{conversation_id}")
def conversation_analytics(conversation_id: str) -> dict:
    """Per-conversation analytics: outcome, decision timing, frustration curve, tips, latency, cost."""
    conversation = mongo.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return analytics.conversation_detail(conversation)


@router.get("/overview")
def analytics_overview() -> dict:
    """Overview tab: total calls, pass/fail/stop rates, decision speed, cost."""
    return analytics.overview(mongo.db)


@router.get("/trends")
def analytics_trends(days: int = Query(30, ge=1, le=365)) -> list[dict]:
    """Trends tab: daily calls, pass rate, decision speed, and frustration."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return analytics.trends(mongo.db, since)


@router.get("/risk")
def analytics_risk() -> dict:
    """Risk tab: fail rate by scenario and difficulty, and red flags on failed calls."""
    return analytics.risk(mongo.db, settings.analytics_min_group_size)


@router.get("/wellbeing")
def analytics_wellbeing() -> dict:
    """Wellbeing tab: safe-word stops, peak frustration, and how calls ended."""
    return analytics.wellbeing(mongo.db)


@router.get("/operations")
def analytics_operations() -> dict:
    """Operations tab: cost per call, voice minutes, and response latency."""
    return analytics.operations(mongo.db)
