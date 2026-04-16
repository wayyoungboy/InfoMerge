"""LLM provider for message analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 20


@dataclass
class MessageAnalysis:
    sentiment: float      # -1.0 ~ 1.0
    topics: list[str]     # 1-3 topic tags
    relevance: float      # 0.0 ~ 1.0


class LLMProvider:
    """OpenAI-compatible API provider for batch message analysis."""

    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def analyze_messages(
        self, messages: list[dict], batch_size: int = BATCH_SIZE
    ) -> list[MessageAnalysis]:
        if not messages:
            return []

        all_results: list[MessageAnalysis] = []
        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]
            raw = await self._call_llm(batch)
            parsed = self._parse_response(raw)
            all_results.extend(parsed)
        return all_results

    async def _call_llm(self, messages: list[dict]) -> str:
        system_prompt = _build_analysis_prompt(
            industry=messages[0].get("_industry_hint", "")
        )
        user_content = json.dumps([
            {"title": m.get("title", ""), "content": m.get("content", "")}
            for m in messages
        ], ensure_ascii=False)

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(self, raw: str) -> list[MessageAnalysis]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {raw[:200]}")
            return []

        results = []
        for item in items:
            try:
                results.append(MessageAnalysis(
                    sentiment=float(item.get("sentiment", 0)),
                    topics=item.get("topics", []),
                    relevance=float(item.get("relevance", 0)),
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid analysis item: {e}")
        return results


def get_llm_provider() -> LLMProvider | None:
    if not settings.llm_api_key or not settings.llm_api_base:
        return None
    return LLMProvider(
        api_base=settings.llm_api_base,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


def _build_analysis_prompt(industry: str) -> str:
    return f"""You are an industry analyst. Analyze the following news articles related to "{industry}".

For EACH article, return a JSON object with:
- "sentiment": float from -1.0 (very negative) to 1.0 (very positive)
- "topics": list of 1-3 short topic tags (in Chinese if content is Chinese)
- "relevance": float from 0.0 to 1.0, how relevant this article is to "{industry}"

Return ONLY a JSON array. No explanation. No markdown.

Example output:
[
  {{"sentiment": 0.7, "topics": ["大模型", "医疗AI"], "relevance": 0.95}},
  {{"sentiment": -0.3, "topics": ["监管", "数据安全"], "relevance": 0.6}}
]
"""
