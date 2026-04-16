"""Industry discovery via LLM classification of messages."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from src.database import get_collection

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredIndustry:
    industry: str
    message_count: int = 0


async def discover_industries(llm_provider=None) -> list[DiscoveredIndustry]:
    """Analyze recent messages to discover industry categories."""
    from src.analysis.llm_provider import get_llm_provider as _get_provider

    provider = llm_provider
    if provider is None:
        provider = _get_provider()
    if provider is None:
        return []

    collection = get_collection()
    result = collection.query(query_texts=["热点 行业 趋势"], n_results=200)

    messages = _format_for_discovery(result)
    if not messages:
        return []

    raw = await provider._call_llm(_build_discovery_messages(messages))
    industries = _parse_discovery_response(raw)

    return industries


def _format_for_discovery(result: dict) -> list[dict]:
    ids = result.get("ids", [])
    if not ids:
        return []
    is_flat = ids and isinstance(ids[0], str)
    id_list = ids[0] if not is_flat else ids
    doc_list = (result.get("documents") or [[]])[0] if not is_flat else (result.get("documents") or [])
    meta_list = (result.get("metadatas") or [[]])[0] if not is_flat else (result.get("metadatas") or [])

    messages = []
    for i, doc_id in enumerate(id_list):
        meta = meta_list[i] if i < len(meta_list) else {}
        messages.append({
            "title": meta.get("title", ""),
            "content": doc_list[i] if i < len(doc_list) else "",
        })
    return messages


def _build_discovery_messages(messages: list[dict]) -> dict:
    content = json.dumps(messages[:50], ensure_ascii=False)
    return {
        "role": "user",
        "content": f"""Analyze these news articles and identify the top industries they belong to.
Return a JSON array with: "industry" (Chinese name), "message_count" (estimated).
Return ONLY the JSON array.

Articles:
{content}""",
    }


def _parse_discovery_response(raw: str) -> list[DiscoveredIndustry]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return []

    return [
        DiscoveredIndustry(
            industry=item.get("industry", ""),
            message_count=item.get("message_count", 0),
        )
        for item in items
        if item.get("industry")
    ]
