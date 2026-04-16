"""seekdb database service using pyseekdb SDK."""

from __future__ import annotations

import logging
from typing import Any

import pyseekdb

from src.channels.models import Message
from src.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "messages"

_admin: pyseekdb.AdminClient | None = None
_client: pyseekdb.Client | None = None
_collection: pyseekdb.Collection | None = None


def get_admin() -> pyseekdb.AdminClient:
    global _admin
    if _admin is None:
        _admin = pyseekdb.AdminClient(path=settings.seekdb_db_path)
    return _admin


def get_client() -> pyseekdb.Client:
    global _client
    if _client is None:
        _client = pyseekdb.Client(
            path=settings.seekdb_db_path,
            database="infomerge",
        )
    return _client


def get_collection() -> pyseekdb.Collection:
    global _collection
    if _collection is None:
        _collection = get_client().get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def init_db() -> None:
    """Initialize database and collection."""
    admin = get_admin()
    try:
        admin.create_database("infomerge")
    except Exception:
        pass
    get_collection()
    logger.info("seekdb initialized")


def save_messages(messages: list[Message]) -> int:
    """Save messages to seekdb. Auto-vectorized by SDK."""
    if not messages:
        return 0

    collection = get_collection()
    ids = [m.doc_id() for m in messages]
    documents = [m.to_document() for m in messages]
    metadatas = [m.to_metadata() for m in messages]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info(f"Saved {len(messages)} messages to seekdb")
    return len(messages)


def search_semantic(query: str, channel: str | None = None, n_results: int = 20) -> list[dict]:
    """Semantic search (vector KNN)."""
    collection = get_collection()
    where = {"channel": channel} if channel else None
    result = collection.query(query_texts=[query], n_results=n_results, where=where)
    return _format_results(result)


def search_fulltext(query: str, channel: str | None = None, n_results: int = 20) -> list[dict]:
    """Full-text keyword search."""
    collection = get_collection()
    where = {"channel": channel} if channel else None
    result = collection.query(where_document={"$contains": query}, n_results=n_results, where=where)
    return _format_results(result)


def search_hybrid(query: str, keywords: str | None = None, channel: str | None = None, n_results: int = 20) -> list[dict]:
    """Hybrid search: vector + full-text with RRF fusion."""
    collection = get_collection()
    where = {"channel": channel} if channel else None

    result = collection.hybrid_search(
        knn={"query_texts": [query], "n_results": n_results, **({"where": where} if where else {})},
        query={"where_document": {"$contains": keywords or query}, "n_results": n_results, **({"where": where} if where else {})},
        rank={"rrf": {}},
        n_results=n_results,
    )
    return _format_results(result)


def get_message_by_id(doc_id: str) -> dict | None:
    """Get a single message by document ID."""
    collection = get_collection()
    result = collection.get(ids=[doc_id])
    if not result["ids"] or not result["ids"][0]:
        return None
    return _format_single(result)


def get_message_count(channel: str | None = None) -> int:
    """Get total message count, optionally filtered by channel."""
    collection = get_collection()
    return collection.count()


def _format_results(result: dict) -> list[dict]:
    """Format pyseekdb query result to API response format."""
    items = []
    if not result["ids"] or not result["ids"][0]:
        return items

    for i, doc_id in enumerate(result["ids"][0]):
        meta = result["metadatas"][0][i] if result.get("metadatas") else {}
        distance = result["distances"][0][i] if result.get("distances") and result["distances"][0] else None
        items.append({
            "id": doc_id,
            "channel": meta.get("channel", ""),
            "title": meta.get("title", ""),
            "content": result["documents"][0][i] if result.get("documents") else "",
            "author": meta.get("author", ""),
            "url": meta.get("url", ""),
            "published_at": meta.get("published_at", ""),
            "score": round(1.0 - distance, 4) if distance is not None else None,
        })
    return items


def _format_single(result: dict) -> dict:
    """Format single message result."""
    if not result["ids"] or not result["ids"][0]:
        return {}
    meta = result["metadatas"][0][0] if result.get("metadatas") else {}
    return {
        "id": result["ids"][0][0],
        "channel": meta.get("channel", ""),
        "title": meta.get("title", ""),
        "content": result["documents"][0][0] if result.get("documents") else "",
        "author": meta.get("author", ""),
        "url": meta.get("url", ""),
        "published_at": meta.get("published_at", ""),
    }
