# Industry Vitality Index Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an industry vitality index analysis feature that uses LLM to analyze collected messages and compute a composite vitality score with 4 dimensions (activity, sentiment, diversity, trend).

**Architecture:** New `src/analysis/` package with LLM provider abstraction, index computation engine, and SQLite persistence. New `/api/vitality/*` endpoints. New `/vitality` frontend page.

**Tech Stack:** Python httpx (LLM calls), SQLite (persistence), FastAPI, React+TypeScript frontend.

---

## File Map

**New files:**
- `src/analysis/__init__.py` — exports
- `src/analysis/llm_provider.py` — LLM provider interface + OpenAI-compatible impl
- `src/analysis/engine.py` — index computation (4 dimensions)
- `src/analysis/store.py` — SQLite persistence layer
- `src/analysis/discoverer.py` — industry discovery via LLM
- `src/api/vitality.py` — FastAPI router for vitality endpoints
- `web/src/pages/VitalityPage.tsx` — vitality analysis page
- `tests/test_analysis/__init__.py`
- `tests/test_analysis/test_llm_provider.py` — LLM provider tests
- `tests/test_analysis/test_engine.py` — engine computation tests
- `tests/test_analysis/test_store.py` — SQLite CRUD tests
- `tests/test_vitality_api.py` — E2E API tests

**Modified files:**
- `src/config.py` — add LLM config fields
- `src/models.py` — add Pydantic request/response models
- `.env.example` — add LLM config template
- `src/main.py` — register vitality router, init analysis in lifespan
- `web/src/api.ts` — add vitality API functions
- `web/src/App.tsx` — add /vitality route + nav link

---

### Task 1: Configuration + Pydantic Models

**Files:**
- Modify: `src/config.py`
- Modify: `src/models.py`
- Modify: `.env.example`

- [ ] **Step 1: Extend Settings in config.py**

Add LLM configuration fields to the Settings class in `src/config.py`:

```python
class Settings(BaseSettings):
    """Loaded from .env file."""

    tavily_api_key: str = ""
    seekdb_db_path: str = "./data/seekdb.db"
    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

- [ ] **Step 2: Update .env.example**

```
TAVILY_API_KEY=
SEEKDB_DB_PATH=./data/seekdb.db
LLM_API_BASE=
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
```

- [ ] **Step 3: Add vitality Pydantic models to models.py**

Append to `src/models.py`:

```python
class VitalityResult(BaseModel):
    industry: str
    total_score: float
    activity_score: float
    sentiment_score: float
    diversity_score: float
    trend_score: float
    analyzed_at: str
    period_start: str
    period_end: str
    message_count: int


class VitalityAnalyzeRequest(BaseModel):
    industry: str = Field(..., description="Industry keyword")
    period_days: int = Field(default=7, ge=1, le=90)
    max_messages: int = Field(default=100, ge=1, le=1000)


class VitalityListResponse(BaseModel):
    industries: list[VitalityResult]


class PaperResult(BaseModel):
    title: str
    authors: str
    abstract: str
    url: str
    published_at: str


class VitalityHistoryResponse(BaseModel):
    industry: str
    results: list[VitalityResult]
```

- [ ] **Step 4: Verify no syntax errors**

Run: `python -c "from src.models import VitalityResult; print('OK')"`
Expected: OK

---

### Task 2: LLM Provider Interface

**Files:**
- Create: `src/analysis/__init__.py`
- Create: `src/analysis/llm_provider.py`
- Create: `tests/test_analysis/__init__.py`
- Test: `tests/test_analysis/test_llm_provider.py`

- [ ] **Step 1: Create package init**

`src/analysis/__init__.py`:
```python
from src.analysis.llm_provider import LLMProvider, MessageAnalysis, get_llm_provider

__all__ = ["LLMProvider", "MessageAnalysis", "get_llm_provider"]
```

- [ ] **Step 2: Write LLM provider test first**

`tests/test_analysis/test_llm_provider.py`:

```python
"""Tests for LLM provider interface and message analysis."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from src.analysis.llm_provider import MessageAnalysis, OpenAIProvider, get_llm_provider


class TestMessageAnalysis:
    def test_fields(self):
        a = MessageAnalysis(sentiment=0.8, topics=["AI", "医疗"], relevance=0.95)
        assert a.sentiment == 0.8
        assert a.topics == ["AI", "医疗"]
        assert a.relevance == 0.95


class TestOpenAIProvider:
    def _make_provider(self):
        return OpenAIProvider(
            api_base="https://api.test.com/v1",
            api_key="test-key",
            model="gpt-4o-mini",
        )

    @pytest.mark.asyncio
    async def test_analyze_messages_empty(self):
        provider = self._make_provider()
        with patch.object(provider, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "[]"
            results = await provider.analyze_messages([])
            assert results == []

    @pytest.mark.asyncio
    async def test_analyze_messages_parses_json(self):
        provider = self._make_provider()
        fake_response = json.dumps([
            {"sentiment": 0.5, "topics": ["AI"], "relevance": 0.9}
        ])
        with patch.object(provider, "_call_llm", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = fake_response
            results = await provider.analyze_messages([{"title": "Test", "content": "test"}])
            assert len(results) == 1
            assert results[0].sentiment == 0.5
            assert results[0].topics == ["AI"]

    @pytest.mark.asyncio
    async def test_analyze_messages_batches(self):
        provider = self._make_provider()
        call_count = 0

        async def fake_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return json.dumps([])

        with patch.object(provider, "_call_llm", new_callable=AsyncMock, side_effect=fake_call):
            messages = [{"title": f"msg{i}", "content": f"content{i}"} for i in range(50)]
            await provider.analyze_messages(messages, batch_size=20)
            assert call_count == 3  # 50 / 20 = 3 batches

    def test_get_llm_provider_no_config_returns_none(self):
        with patch("src.analysis.llm_provider.settings") as mock_settings:
            mock_settings.llm_api_key = ""
            assert get_llm_provider() is None


class TestBuildAnalysisPrompt:
    def test_prompt_structure(self):
        from src.analysis.llm_provider import _build_analysis_prompt
        prompt = _build_analysis_prompt(industry="人工智能")
        assert "人工智能" in prompt
        assert "sentiment" in prompt
        assert "topics" in prompt
        assert "relevance" in prompt
```

- [ ] **Step 3: Run test to verify failures**

Run: `cd /data/code/InfoMerge && .venv/bin/python -m pytest tests/test_analysis/test_llm_provider.py -v`
Expected: All FAIL (module not found)

- [ ] **Step 4: Implement LLM provider**

Create `src/analysis/llm_provider.py`:

```python
"""LLM provider for message analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

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
        self, messages: list[dict[str, Any]], batch_size: int = BATCH_SIZE
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

    async def _call_llm(self, messages: list[dict[str, Any]]) -> str:
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
        # Strip markdown code fences if present
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
```

- [ ] **Step 5: Run test to verify all pass**

Run: `.venv/bin/python -m pytest tests/test_analysis/test_llm_provider.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/analysis/__init__.py src/analysis/llm_provider.py tests/test_analysis/__init__.py tests/test_analysis/test_llm_provider.py
git commit -m "feat: add LLM provider interface for message analysis"
```

---

### Task 3: Index Computation Engine

**Files:**
- Create: `src/analysis/engine.py`
- Test: `tests/test_analysis/test_engine.py`

- [ ] **Step 1: Write engine test first**

`tests/test_analysis/test_engine.py`:

```python
"""Tests for vitality index computation engine."""

import math
from src.analysis.engine import (
    compute_activity_score,
    compute_sentiment_score,
    compute_diversity_score,
    compute_trend_score,
    compute_vitality_index,
)


class TestActivityScore:
    def test_zero_messages(self):
        assert compute_activity_score(0, []) == 0.0

    def test_high_volume_even_distribution(self):
        # 10 messages evenly spread across hours
        timestamps = [f"2026-04-17T{i:02d}:00:00" for i in range(10)]
        score = compute_activity_score(10, timestamps)
        assert 70 <= score <= 100

    def test_clustered_distribution(self):
        # All messages at same hour
        timestamps = ["2026-04-17T10:00:00"] * 5
        score = compute_activity_score(5, timestamps)
        assert score < 60  # low evenness bonus


class TestSentimentScore:
    def test_all_positive(self):
        scores = compute_sentiment_score([0.8, 0.9, 0.7])
        assert scores > 80

    def test_all_negative(self):
        scores = compute_sentiment_score([-0.8, -0.9, -0.7])
        assert scores < 30

    def test_neutral(self):
        scores = compute_sentiment_score([0.0, 0.0, 0.0])
        assert 40 <= scores <= 60

    def test_empty(self):
        assert compute_sentiment_score([]) == 50.0


class TestDiversityScore:
    def test_many_topics(self):
        all_topics = ["AI", "医疗", "监管", "投资", "人才", "政策", "技术", "市场"]
        assert compute_diversity_score(all_topics) == 80.0  # min(8/10, 1.0) * 100

    def test_few_topics(self):
        assert compute_diversity_score(["AI", "医疗"]) == 20.0

    def test_no_topics(self):
        assert compute_diversity_score([]) == 0.0


class TestTrendScore:
    def test_growth(self):
        assert compute_trend_score(20, 10) > 70

    def test_decline(self):
        assert compute_trend_score(5, 15) < 30

    def test_same(self):
        assert compute_trend_score(10, 10) == 50.0

    def test_no_previous(self):
        assert compute_trend_score(10, 0) == 50.0


class TestVitalityIndex:
    def test_combined_scores(self):
        result = compute_vitality_index(
            activity=80,
            sentiment=70,
            diversity=60,
            trend=50,
        )
        # 80*0.3 + 70*0.25 + 60*0.2 + 50*0.25 = 24 + 17.5 + 12 + 12.5 = 66.0
        assert result == 66.0
```

- [ ] **Step 2: Run test to verify failures**

Run: `.venv/bin/python -m pytest tests/test_analysis/test_engine.py -v`
Expected: All FAIL

- [ ] **Step 3: Implement engine**

Create `src/analysis/engine.py`:

```python
"""Vitality index computation engine."""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta

from src.analysis.llm_provider import MessageAnalysis


def compute_activity_score(
    message_count: int,
    message_timestamps: list[str],
) -> float:
    """Activity score: volume (0-80) + time evenness (0-20)."""
    if message_count == 0:
        return 0.0

    # Volume score: log-scaled, max 80
    volume = min(80.0, math.log(message_count + 1) / math.log(101) * 80)

    # Time evenness: group messages by hour, compute std deviation
    hours: list[int] = []
    for ts in message_timestamps:
        try:
            dt = datetime.fromisoformat(ts)
            hours.append(dt.hour)
        except (ValueError, TypeError):
            hours.append(0)

    if len(hours) < 2:
        evenness = 10.0  # neutral
    else:
        hour_counts = Counter(hours)
        values = list(hour_counts.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        # Lower std = more even = higher score. Normalize: std=0 → 20, std=mean → 0
        evenness = max(0.0, min(20.0, 20.0 * (1 - std / max(mean, 1))))

    return round(volume + evenness, 2)


def compute_sentiment_score(analyses: list[MessageAnalysis]) -> float:
    """Sentiment score: 0-100 based on sentiment distribution."""
    if not analyses:
        return 50.0

    sentiments = [a.sentiment for a in analyses]
    avg_sentiment = sum(sentiments) / len(sentiments)
    positive_ratio = sum(1 for s in sentiments if s > 0.1) / len(sentiments)

    # (positive_ratio * 100 + avg_sentiment * 50 + 100) / 2
    score = (positive_ratio * 100 + avg_sentiment * 50 + 100) / 2
    return round(max(0.0, min(100.0, score)), 2)


def compute_diversity_score(all_topics: list[str]) -> float:
    """Topic diversity: unique topics / 10, capped at 100."""
    unique = len(set(all_topics))
    return round(min(unique / 10.0, 1.0) * 100, 2)


def compute_trend_score(current_count: int, previous_count: int) -> float:
    """Trend score: growth rate mapped to 0-100 via sigmoid."""
    if previous_count == 0:
        return 50.0

    growth = (current_count - previous_count) / max(previous_count, 1)
    # Sigmoid: maps (-inf, +inf) to (0, 1), shifted so growth=0 → 0.5
    normalized = 1 / (1 + math.exp(-growth * 2))
    return round(normalized * 100, 2)


def compute_vitality_index(
    activity: float,
    sentiment: float,
    diversity: float,
    trend: float,
) -> float:
    """Weighted composite: activity*0.3 + sentiment*0.25 + diversity*0.2 + trend*0.25."""
    total = activity * 0.30 + sentiment * 0.25 + diversity * 0.20 + trend * 0.25
    return round(max(0.0, min(100.0, total)), 2)
```

- [ ] **Step 4: Run test to verify all pass**

Run: `.venv/bin/python -m pytest tests/test_analysis/test_engine.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/analysis/engine.py tests/test_analysis/test_engine.py
git commit -m "feat: add vitality index computation engine"
```

---

### Task 4: SQLite Persistence Layer

**Files:**
- Create: `src/analysis/store.py`
- Test: `tests/test_analysis/test_store.py`

- [ ] **Step 1: Write store test first**

`tests/test_analysis/test_store.py`:

```python
"""Tests for vitality SQLite persistence."""

import pytest
from pathlib import Path

from src.analysis.store import VitalityStore


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "test_vitality.db")
    s = VitalityStore(db_path)
    yield s
    s.close()


class TestVitalityStore:
    def test_save_and_get_latest(self, store):
        store.save_result(
            industry="人工智能",
            total_score=75.5,
            activity_score=80.0,
            sentiment_score=70.0,
            diversity_score=65.0,
            trend_score=50.0,
            period_start="2026-04-10",
            period_end="2026-04-17",
            message_count=42,
        )
        result = store.get_latest("人工智能")
        assert result is not None
        assert result["industry"] == "人工智能"
        assert result["total_score"] == 75.5

    def test_get_history(self, store):
        store.save_result("AI", 70, 75, 65, 60, 50, "2026-04-03", "2026-04-10", 30)
        store.save_result("AI", 75, 80, 70, 65, 55, "2026-04-10", "2026-04-17", 42)
        history = store.get_history("AI")
        assert len(history) == 2

    def test_list_industries(self, store):
        store.save_result("AI", 70, 75, 65, 60, 50, "2026-04-10", "2026-04-17", 30)
        store.save_result("新能源", 80, 85, 75, 70, 55, "2026-04-10", "2026-04-17", 50)
        industries = store.list_industries()
        assert len(industries) == 2

    def test_get_latest_not_found(self, store):
        assert store.get_latest("不存在") is None

    def test_empty_history(self, store):
        assert store.get_history("none") == []

    def test_close(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        s = VitalityStore(db_path)
        s.close()
        # Double close should be safe
        s.close()
```

- [ ] **Step 2: Run test to verify failures**

Run: `.venv/bin/python -m pytest tests/test_analysis/test_store.py -v`
Expected: All FAIL

- [ ] **Step 3: Implement store**

Create `src/analysis/store.py`:

```python
"""SQLite persistence for vitality index results."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS vitality_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT NOT NULL,
    total_score REAL,
    activity_score REAL,
    sentiment_score REAL,
    diversity_score REAL,
    trend_score REAL,
    analyzed_at TEXT,
    period_start TEXT,
    period_end TEXT,
    message_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_vitality_industry_time
    ON vitality_results(industry, period_end);
"""


class VitalityStore:
    """SQLite store for vitality index results."""

    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(CREATE_TABLES)

    def save_result(
        self,
        industry: str,
        total_score: float,
        activity_score: float,
        sentiment_score: float,
        diversity_score: float,
        trend_score: float,
        period_start: str,
        period_end: str,
        message_count: int,
    ) -> int:
        row = self.conn.execute(
            """INSERT INTO vitality_results
               (industry, total_score, activity_score, sentiment_score,
                diversity_score, trend_score, analyzed_at,
                period_start, period_end, message_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                industry, total_score, activity_score, sentiment_score,
                diversity_score, trend_score, datetime.now().isoformat(),
                period_start, period_end, message_count,
            ),
        )
        self.conn.commit()
        return row.lastrowid

    def get_latest(self, industry: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM vitality_results WHERE industry=? ORDER BY period_end DESC LIMIT 1",
            (industry,),
        ).fetchone()
        return dict(row) if row else None

    def get_history(self, industry: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM vitality_results WHERE industry=? ORDER BY period_end ASC",
            (industry,),
        ).fetchall()
        return [dict(r) for r in rows]

    def list_industries(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT v.* FROM vitality_results v
               INNER JOIN (
                   SELECT industry, MAX(period_end) as max_end
                   FROM vitality_results GROUP BY industry
               ) latest ON v.industry = latest.industry AND v.period_end = latest.max_end
               ORDER BY v.total_score DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
```

- [ ] **Step 4: Run test to verify all pass**

Run: `.venv/bin/python -m pytest tests/test_analysis/test_store.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/analysis/store.py tests/test_analysis/test_store.py
git commit -m "feat: add SQLite persistence for vitality results"
```

---

### Task 5: Industry Discoverer

**Files:**
- Create: `src/analysis/discoverer.py`

- [ ] **Step 1: Implement discoverer**

Create `src/analysis/discoverer.py`:

```python
"""Industry discovery via LLM classification of messages."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from src.database import get_collection

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredIndustry:
    industry: str
    message_count: int = 0


async def discover_industries(llm_provider) -> list[DiscoveredIndustry]:
    """Analyze recent messages to discover industry categories."""
    from src.analysis.llm_provider import get_llm_provider as _get_provider

    provider = llm_provider
    if provider is None:
        provider = _get_provider()
    if provider is None:
        return []

    # Fetch recent messages from seekdb
    collection = get_collection()
    result = collection.query(query_texts=["热点 行业 趋势"], n_results=200)

    messages = _format_for_discovery(result)
    if not messages:
        return []

    # Ask LLM to identify industries
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
    content = json.dumps(messages[:50], ensure_ascii=False)  # cap at 50 for discovery
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
```

No test for discoverer — it's a thin wrapper that depends on LLM and seekdb; tested via E2E in Task 7.

- [ ] **Step 2: Commit**

```bash
git add src/analysis/discoverer.py
git commit -m "feat: add industry discovery via LLM"
```

---

### Task 6: Vitality API Router

**Files:**
- Create: `src/api/vitality.py`
- Modify: `src/main.py`

- [ ] **Step 1: Write E2E test for vitality API**

Add to `tests/test_vitality_api.py`:

```python
"""E2E tests for vitality API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.models import VitalityAnalyzeRequest


class TestVitalityAPI:
    @pytest.fixture
    def client(self):
        """Test client with mocked DB and empty vitality store."""
        from unittest.mock import patch, MagicMock
        from fastapi.testclient import TestClient
        mock_collection = MagicMock()
        mock_collection.query.return_value = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        mock_collection.hybrid_search.return_value = mock_collection.query.return_value
        mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
        mock_collection.count.return_value = 0
        with patch("src.database.init_db"), \
             patch("src.database.save_messages", return_value=0), \
             patch("src.database.get_collection", return_value=mock_collection):
            from src.main import app
            yield TestClient(app)

    def test_health(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_vitality_list_empty(self, client):
        res = client.get("/api/vitality/list")
        assert res.status_code == 200
        assert res.json()["industries"] == []

    def test_vitality_history_empty(self, client):
        res = client.get("/api/vitality/history/nonexistent")
        assert res.status_code == 200
        assert res.json()["results"] == []

    def test_analyze_no_llm_config(self, client):
        res = client.post("/api/vitality/analyze", json={
            "industry": "人工智能",
            "period_days": 7,
        })
        # Should return 400 or 500 when LLM not configured
        assert res.status_code in (400, 500)
```

- [ ] **Step 2: Run test to verify failures**

Run: `.venv/bin/python -m pytest tests/test_vitality_api.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement vitality router**

Create `src/api/vitality.py`:

```python
"""Vitality index API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from src.database import get_collection
from src.models import VitalityResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitality", tags=["vitality"])

_vitality_store = None  # injected by main.py


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
    from src.analysis.llm_provider import get_llm_provider
    from src.analysis.engine import (
        compute_activity_score,
        compute_sentiment_score,
        compute_diversity_score,
        compute_trend_score,
        compute_vitality_index,
    )

    llm = get_llm_provider()
    if llm is None:
        raise HTTPException(status_code=400, detail="LLM not configured. Set LLM_API_BASE and LLM_API_KEY.")

    messages = _get_messages_for_industry(req.industry, req.period_days, req.max_messages)
    if not messages:
        return {"error": "No messages found for industry", "scores": None}

    # Analyze with LLM
    analyses = await llm.analyze_messages(messages)

    # Compute scores
    timestamps = [m.get("published_at", "") for m in messages]
    all_topics = []
    for a in analyses:
        all_topics.extend(a.topics)

    activity = compute_activity_score(len(messages), timestamps)
    sentiment = compute_sentiment_score(analyses)
    diversity = compute_diversity_score(all_topics)

    # Get previous period count for trend
    prev_messages = _get_messages_for_industry(
        req.industry, req.period_days * 2, req.max_messages
    )
    prev_count = len(prev_messages) - len(messages) if len(prev_messages) > len(messages) else 0
    trend = compute_trend_score(len(messages), prev_count)

    total = compute_vitality_index(activity, sentiment, diversity, trend)

    period_end = datetime.now().isoformat()
    period_start = (datetime.now() - timedelta(days=req.period_days)).isoformat()

    # Save to store
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
    """Search for academic papers related to an industry.
    Note: Paper search MCP is called via HTTP if configured.
    Falls back to empty list if not available.
    """
    # Paper search MCP integration placeholder — returns empty for now
    # Can be wired later via MCP HTTP endpoint
    return {"papers": [], "industry": industry}
```

- [ ] **Step 4: Register router in main.py**

Modify `src/main.py`. Add after existing router imports:

```python
# At top, after existing imports
from src.analysis.store import VitalityStore

# Before app definition, initialize store
_vitality_db_path = "./data/vitality.db"
vitality_store = VitalityStore(_vitality_db_path)

# Inside lifespan, on shutdown:
# After scheduler.shutdown(), add:
vitality_store.close()
```

Replace the router section to include:

```python
from src.api.channels import router as channels_router
from src.api.search import router as search_router
from src.api.vitality import router as vitality_router, set_store

app.include_router(channels_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(vitality_router, prefix="/api")

# Inject store
set_store(vitality_store)
```

Full modified `src/main.py` (replace entire file):

```python
"""FastAPI application entry point."""

import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.channels.plugins.tavily.channel import TavilyChannel  # noqa: F401
from src.channels.plugins.webhook.channel import WebhookChannel  # noqa: F401
from src.channels.registry import registry
from src.database import init_db
from src.services import scheduler
from src.analysis.store import VitalityStore

config_store: dict = {}
vitality_store = VitalityStore("./data/vitality.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    init_db()

    plugins_dir = pathlib.Path(__file__).parent / "channels" / "plugins"
    registry.auto_discover(plugins_dir)

    scheduler.start()
    yield
    scheduler.shutdown()
    vitality_store.close()


app = FastAPI(title="InfoMerge", description="Multi-source hot topic collection and analysis platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

import src.api.channels as channels_module
channels_module.config_store = config_store

from src.api.channels import router as channels_router
from src.api.search import router as search_router
from src.api.vitality import router as vitality_router, set_store

app.include_router(channels_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(vitality_router, prefix="/api")

set_store(vitality_store)


@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run test to verify passes**

Run: `.venv/bin/python -m pytest tests/test_vitality_api.py -v`
Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All previous + new tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/api/vitality.py src/main.py tests/test_vitality_api.py
git commit -m "feat: add vitality index API endpoints"
```

---

### Task 7: Frontend Vitality Page

**Files:**
- Create: `web/src/pages/VitalityPage.tsx`
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`

- [ ] **Step 1: Add API functions to api.ts**

Append to `web/src/api.ts`:

```typescript
export interface VitalityResult {
  industry: string;
  total_score: number;
  activity_score: number;
  sentiment_score: number;
  diversity_score: number;
  trend_score: number;
  analyzed_at: string;
  period_start: string;
  period_end: string;
  message_count: number;
}

export interface VitalityListResponse {
  industries: VitalityResult[];
}

export interface VitalityHistoryResponse {
  industry: string;
  results: VitalityResult[];
}

export interface PaperResult {
  title: string;
  authors: string;
  abstract: string;
  url: string;
  published_at: string;
}

export interface PaperResponse {
  papers: PaperResult[];
  industry: string;
}

export async function analyzeVitality(
  industry: string,
  periodDays = 7,
  maxMessages = 100
): Promise<VitalityResult | { error: string }> {
  const res = await fetch(`${API_BASE}/vitality/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ industry, period_days: periodDays, max_messages: maxMessages }),
  });
  return res.json();
}

export async function listVitalality(): Promise<VitalityListResponse> {
  const res = await fetch(`${API_BASE}/vitality/list`);
  return res.json();
}

export async function getVitalityHistory(industry: string): Promise<VitalityHistoryResponse> {
  const res = await fetch(`${API_BASE}/vitality/history/${industry}`);
  return res.json();
}

export async function searchPapers(industry: string): Promise<PaperResponse> {
  const res = await fetch(`${API_BASE}/vitality/papers/${industry}`);
  return res.json();
}

export async function discoverIndustries(): Promise<{ industries: Array<{ industry: string; message_count: number }> }> {
  const res = await fetch(`${API_BASE}/vitality/discover`, {
    method: 'POST',
  });
  return res.json();
}
```

- [ ] **Step 2: Create VitalityPage component**

Create `web/src/pages/VitalityPage.tsx`:

```typescript
import { useCallback, useEffect, useState } from 'react';
import { analyzeVitality, discoverIndustries, listVitalality, searchPapers, VitalityResult, PaperResult } from '../api';

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ marginBottom: '4px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#8b949e' }}>
        <span>{label}</span>
        <span style={{ fontFamily: '"JetBrains Mono", monospace' }}>{value.toFixed(1)}</span>
      </div>
      <div style={{ height: '4px', background: '#21262d', borderRadius: '2px' }}>
        <div style={{ width: `${Math.min(value, 100)}%`, height: '100%', background: color, borderRadius: '2px' }} />
      </div>
    </div>
  );
}

function VitalityCard({ result, onClick }: { result: VitalityResult; onClick: () => void }) {
  const scoreColor = result.total_score >= 70 ? '#238636' : result.total_score >= 40 ? '#9e6a03' : '#f85149';
  return (
    <div
      onClick={onClick}
      style={{
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '8px',
        padding: '16px',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: '#e6edf3' }}>{result.industry}</h3>
        <span style={{
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '24px',
          fontWeight: 700,
          color: scoreColor,
        }}>
          {result.total_score.toFixed(1)}
        </span>
      </div>
      <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '8px' }}>
        消息数: {result.message_count} | 分析: {result.analyzed_at?.slice(0, 19)}
      </div>
      <ScoreBar label="活跃度" value={result.activity_score} color="#58a6ff" />
      <ScoreBar label="情感" value={result.sentiment_score} color="#238636" />
      <ScoreBar label="多样性" value={result.diversity_score} color="#9e6a03" />
      <ScoreBar label="趋势" value={result.trend_score} color="#1f6feb" />
    </div>
  );
}

function PaperCard({ paper }: { paper: PaperResult }) {
  return (
    <div style={{
      background: '#161b22',
      border: '1px solid #30363d',
      borderRadius: '8px',
      padding: '12px',
      marginBottom: '8px',
    }}>
      <h4 style={{ margin: '0 0 4px', fontSize: '14px', color: '#58a6ff' }}>
        {paper.url ? (
          <a href={paper.url} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
            {paper.title}
          </a>
        ) : paper.title}
      </h4>
      <p style={{ margin: 0, fontSize: '12px', color: '#8b949e' }}>
        {paper.abstract?.slice(0, 150)}{paper.abstract?.length > 150 ? '...' : ''}
      </p>
    </div>
  );
}

export default function VitalityPage() {
  const [industries, setIndustries] = useState<VitalityResult[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('');
  const [industryInput, setIndustryInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);
  const [papers, setPapers] = useState<PaperResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<VitalityResult | null>(null);

  const loadVitality = useCallback(async () => {
    try {
      const res = await listVitalality();
      setIndustries(res.industries);
    } catch (err) {
      console.error('Failed to load vitality:', err);
    }
  }, []);

  useEffect(() => {
    loadVitality();
  }, [loadVitality]);

  const handleAnalyze = async () => {
    if (!industryInput.trim()) return;
    setLoading(true);
    try {
      const result = await analyzeVitality(industryInput);
      if ('error' in result) {
        alert(result.error);
      } else {
        setSelectedResult(result);
        loadVitality();
      }
    } catch {
      alert('分析请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await discoverIndustries();
      if (res.industries?.length > 0) {
        setIndustryInput(res.industries[0].industry);
      }
    } catch {
      alert('行业发现失败');
    } finally {
      setDiscovering(false);
    }
  };

  const handleSelectIndustry = async (industry: string) => {
    setSelectedIndustry(industry);
    try {
      const res = await searchPapers(industry);
      setPapers(res.papers);
    } catch {
      setPapers([]);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: '20px', marginBottom: '16px' }}>行业活力指数</h1>

      {/* Input section */}
      <div style={{
        background: '#161b22',
        border: '1px solid #30363d',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={industryInput}
            onChange={(e) => setIndustryInput(e.target.value)}
            placeholder="输入行业关键词..."
            style={{
              flex: 1,
              background: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              padding: '8px 12px',
              color: '#e6edf3',
              fontSize: '13px',
              outline: 'none',
            }}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              background: loading ? '#30363d' : '#1f6feb',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '分析中...' : '分析'}
          </button>
          <button
            onClick={handleDiscover}
            disabled={discovering}
            style={{
              background: discovering ? '#30363d' : '#238636',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              cursor: discovering ? 'not-allowed' : 'pointer',
            }}
          >
            {discovering ? '发现中...' : '自动发现'}
          </button>
        </div>
      </div>

      {/* Selected industry detail */}
      {selectedResult && (
        <div style={{
          background: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '16px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '18px', color: '#e6edf3' }}>{selectedResult.industry}</h3>
            <span style={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '32px',
              fontWeight: 700,
              color: selectedResult.total_score >= 70 ? '#238636' : selectedResult.total_score >= 40 ? '#9e6a03' : '#f85149',
            }}>
              {selectedResult.total_score.toFixed(1)}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
            <ScoreBar label="活跃度" value={selectedResult.activity_score} color="#58a6ff" />
            <ScoreBar label="情感倾向" value={selectedResult.sentiment_score} color="#238636" />
            <ScoreBar label="话题多样性" value={selectedResult.diversity_score} color="#9e6a03" />
            <ScoreBar label="时间趋势" value={selectedResult.trend_score} color="#1f6feb" />
          </div>
        </div>
      )}

      {/* Industry cards grid */}
      {industries.length > 0 && (
        <>
          <h2 style={{ fontSize: '16px', marginBottom: '12px', color: '#8b949e' }}>已分析行业</h2>
          <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
            {industries.map((ind) => (
              <VitalityCard
                key={ind.industry}
                result={ind}
                onClick={() => handleSelectIndustry(ind.industry)}
              />
            ))}
          </div>
        </>
      )}

      {/* Papers section */}
      {selectedIndustry && (
        <div style={{ marginTop: '24px' }}>
          <h2 style={{ fontSize: '16px', marginBottom: '12px', color: '#8b949e' }}>
            相关论文 — {selectedIndustry}
          </h2>
          {papers.length > 0 ? (
            papers.map((p, i) => <PaperCard key={i} paper={p} />)
          ) : (
            <p style={{ color: '#8b949e', textAlign: 'center', padding: '24px 0' }}>暂无论文数据</p>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Update App.tsx with route and nav**

Modify `web/src/App.tsx`. Full replacement:

```typescript
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import ChannelsPage from './pages/ChannelsPage';
import VitalityPage from './pages/VitalityPage';

function Header() {
  const location = useLocation();
  const navStyle = (path: string) => ({
    color: location.pathname === path ? '#58a6ff' : '#8b949e',
    textDecoration: 'none',
    fontSize: '14px' as const,
  });
  return (
    <header style={{
      background: '#161b22',
      borderBottom: '1px solid #30363d',
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: '24px',
    }}>
      <span style={{ color: '#e6edf3', fontWeight: 700, fontSize: '18px' }}>
        InfoMerge
      </span>
      <nav style={{ display: 'flex', gap: '16px' }}>
        <Link to="/" style={navStyle('/')}>搜索</Link>
        <Link to="/vitality" style={navStyle('/vitality')}>活力指数</Link>
        <Link to="/channels" style={navStyle('/channels')}>渠道管理</Link>
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        minHeight: '100vh',
        background: '#0d1117',
        color: '#e6edf3',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}>
        <Header />
        <main style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/vitality" element={<VitalityPage />} />
            <Route path="/channels" element={<ChannelsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Verify frontend compiles**

Run: `cd /data/code/InfoMerge/web && npm run build`
Expected: Build succeeds with no errors

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/VitalityPage.tsx web/src/api.ts web/src/App.tsx
git commit -m "feat: add vitality index frontend page"
```

---

### Task 8: Integration Test + Final Verification

**Files:**
- Modify: `tests/test_vitality_api.py` (add mocked LLM test)

- [ ] **Step 1: Add mocked LLM analysis test**

Append to `tests/test_vitality_api.py`:

```python
class TestVitalityAnalyzeMocked:
    @pytest.mark.asyncio
    async def test_analyze_with_mock_llm(self, client, tmp_vitality_store):
        """Test full analyze flow with mocked LLM."""
        from unittest.mock import patch, AsyncMock
        from src.analysis.llm_provider import MessageAnalysis

        mock_analyses = [
            MessageAnalysis(sentiment=0.7, topics=["AI", "医疗"], relevance=0.9),
            MessageAnalysis(sentiment=0.5, topics=["大模型"], relevance=0.8),
            MessageAnalysis(sentiment=-0.2, topics=["监管"], relevance=0.6),
        ]

        with patch("src.api.vitality.get_llm_provider") as mock_get:
            mock_llm = AsyncMock()
            mock_llm.analyze_messages.return_value = mock_analyses
            mock_get.return_value = mock_llm

            res = client.post("/api/vitality/analyze", json={
                "industry": "人工智能",
                "period_days": 7,
            })
            assert res.status_code == 200
            data = res.json()
            assert "total_score" in data
            assert data["industry"] == "人工智能"
```

This test requires a conftest fixture for the vitality store. Add to `tests/conftest.py`:

```python
@pytest.fixture
def tmp_vitality_store(tmp_path):
    """Create a temporary vitality store and inject it."""
    from src.analysis.store import VitalityStore
    import src.api.vitality as vitality_module
    db_path = str(tmp_path / "test_vitality.db")
    store = VitalityStore(db_path)
    vitality_module.set_store(store)
    yield store
    store.close()
    vitality_module.set_store(None)
```

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: ALL tests PASS (35 existing + new vitality tests)

- [ ] **Step 3: Final commit**

```bash
git add tests/test_vitality_api.py tests/conftest.py
git commit -m "test: add mocked LLM analysis test for vitality API"
```

- [ ] **Step 4: Push to remote**

```bash
git push origin master
```
