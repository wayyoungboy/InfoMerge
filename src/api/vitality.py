"""Vitality index API endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from src.database import get_collection
from src.models import VitalityResult, VitalityAnalyzeRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitality", tags=["vitality"])

_vitality_store = None


def set_store(store) -> None:
    global _vitality_store
    _vitality_store = store


def _get_messages_for_industry(industry: str, days: int, max_msgs: int) -> list[dict]:
    """Fetch messages matching industry keyword from seekdb."""
    collection = get_collection()
    result = collection.query(query_texts=[industry], n_results=max_msgs)

    ids = result.get("ids", [])
    if not ids:
        return []
    is_flat = ids and isinstance(ids[0], str)
    id_list = ids[0] if not is_flat else ids
    doc_list = (result.get("documents") or [[]])[0] if not is_flat else (result.get("documents") or [])
    meta_list = (result.get("metadatas") or [[]])[0] if not is_flat else (result.get("metadatas") or [])

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    messages = []
    for i in range(len(id_list)):
        meta = meta_list[i] if i < len(meta_list) else {}
        pub_at = meta.get("published_at", "")
        if pub_at and pub_at < cutoff:
            continue
        messages.append({
            "title": meta.get("title", ""),
            "content": doc_list[i] if i < len(doc_list) else "",
            "published_at": pub_at,
        })
    return messages


@router.get("/list")
def list_vitality():
    """List all analyzed industries with their latest vitality scores."""
    if _vitality_store is None:
        return {"industries": []}
    industries = _vitality_store.list_industries()
    return {
        "industries": [
            VitalityResult(
                industry=d["industry"],
                total_score=d["total_score"] or 0,
                activity_score=d["activity_score"] or 0,
                sentiment_score=d["sentiment_score"] or 0,
                diversity_score=d["diversity_score"] or 0,
                trend_score=d["trend_score"] or 0,
                analyzed_at=d.get("analyzed_at", ""),
                period_start=d.get("period_start", ""),
                period_end=d.get("period_end", ""),
                message_count=d.get("message_count", 0),
            )
            for d in industries
        ]
    }


@router.get("/history/{industry}")
def vitality_history(industry: str):
    """Get vitality history for an industry."""
    if _vitality_store is None:
        return {"industry": industry, "results": []}
    results = _vitality_store.get_history(industry)
    return {
        "industry": industry,
        "results": [
            VitalityResult(
                industry=d["industry"],
                total_score=d["total_score"] or 0,
                activity_score=d["activity_score"] or 0,
                sentiment_score=d["sentiment_score"] or 0,
                diversity_score=d["diversity_score"] or 0,
                trend_score=d["trend_score"] or 0,
                analyzed_at=d.get("analyzed_at", ""),
                period_start=d.get("period_start", ""),
                period_end=d.get("period_end", ""),
                message_count=d.get("message_count", 0),
            )
            for d in results
        ],
    }


@router.post("/analyze")
async def analyze_vitality(req: VitalityAnalyzeRequest):
    """Trigger industry vitality analysis and return results."""
    from src.analysis.engine import (
        compute_activity_score,
        compute_sentiment_score,
        compute_diversity_score,
        compute_trend_score,
        compute_vitality_index,
    )
    from src.analysis.llm_provider import get_llm_provider

    llm = get_llm_provider()
    if llm is None:
        raise HTTPException(status_code=400, detail="LLM not configured. Set LLM_API_BASE and LLM_API_KEY.")

    messages = _get_messages_for_industry(req.industry, req.period_days, req.max_messages)
    if not messages:
        return {"error": "No messages found for industry"}

    analyses = await llm.analyze_messages(messages)

    timestamps = [m.get("published_at", "") for m in messages]
    all_topics = []
    for a in analyses:
        all_topics.extend(a.topics)

    activity = compute_activity_score(len(messages), timestamps)
    sentiment = compute_sentiment_score(analyses)
    diversity = compute_diversity_score(all_topics)

    prev_count = 0
    trend = compute_trend_score(len(messages), prev_count)

    total = compute_vitality_index(activity, sentiment, diversity, trend)

    period_end = datetime.now().isoformat()
    period_start = (datetime.now() - timedelta(days=req.period_days)).isoformat()

    if _vitality_store:
        _vitality_store.save_result(
            industry=req.industry,
            total_score=total,
            activity_score=activity,
            sentiment_score=sentiment,
            diversity_score=diversity,
            trend_score=trend,
            period_start=period_start,
            period_end=period_end,
            message_count=len(messages),
        )

    return VitalityResult(
        industry=req.industry,
        total_score=total,
        activity_score=activity,
        sentiment_score=sentiment,
        diversity_score=diversity,
        trend_score=trend,
        analyzed_at=period_end,
        period_start=period_start,
        period_end=period_end,
        message_count=len(messages),
    )


@router.post("/discover")
async def discover_industries():
    """Trigger industry discovery via LLM."""
    from src.analysis.discoverer import discover_industries as _discover
    from src.analysis.llm_provider import get_llm_provider

    llm = get_llm_provider()
    if llm is None:
        raise HTTPException(status_code=400, detail="LLM not configured.")

    industries = await _discover(llm)
    return {"industries": [{"industry": ind.industry, "message_count": ind.message_count} for ind in industries]}


@router.get("/papers/{industry}")
def search_papers(industry: str):
    """Search for academic papers related to an industry."""
    return {"papers": [], "industry": industry}
