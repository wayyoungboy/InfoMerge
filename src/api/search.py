"""Search API endpoints."""

from fastapi import APIRouter, HTTPException

from src.database import get_message_by_id, get_message_count, search_fulltext, search_hybrid, search_semantic
from src.models import FulltextSearchRequest, HybridSearchRequest, SearchResult, SearchResponse, SemanticSearchRequest

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SearchResponse)
def semantic_search(req: SemanticSearchRequest):
    results = search_semantic(query=req.query, channel=req.channel, n_results=req.top_k)
    return SearchResponse(total=len(results), results=[SearchResult(**r) for r in results])


@router.post("/fulltext", response_model=SearchResponse)
def fulltext_search(req: FulltextSearchRequest):
    results = search_fulltext(query=req.query, channel=req.channel, n_results=req.top_k)
    return SearchResponse(total=len(results), results=[SearchResult(**r) for r in results])


@router.post("/hybrid", response_model=SearchResponse)
def hybrid_search(req: HybridSearchRequest):
    results = search_hybrid(query=req.query, keywords=req.keywords, channel=req.channel, n_results=req.top_k)
    return SearchResponse(total=len(results), results=[SearchResult(**r) for r in results])


@router.get("/messages/count")
def message_count(channel: str | None = None):
    return {"count": get_message_count(channel)}


@router.get("/messages/{doc_id}")
def get_message(doc_id: str):
    msg = get_message_by_id(doc_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg
