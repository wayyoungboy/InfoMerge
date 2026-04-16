"""Tests for LLM provider interface and message analysis."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from src.analysis.llm_provider import MessageAnalysis, LLMProvider, get_llm_provider


class TestMessageAnalysis:
    def test_fields(self):
        a = MessageAnalysis(sentiment=0.8, topics=["AI", "医疗"], relevance=0.95)
        assert a.sentiment == 0.8
        assert a.topics == ["AI", "医疗"]
        assert a.relevance == 0.95


class TestLLMProvider:
    def _make_provider(self):
        return LLMProvider(
            api_base="https://api.test.com/v1",
            api_key="test-key",
            model="gpt-4o-mini",
        )

    @pytest.mark.asyncio
    async def test_analyze_messages_empty(self):
        provider = self._make_provider()
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
            mock_settings.llm_api_base = ""
            assert get_llm_provider() is None


class TestBuildAnalysisPrompt:
    def test_prompt_structure(self):
        from src.analysis.llm_provider import _build_analysis_prompt
        prompt = _build_analysis_prompt(industry="人工智能")
        assert "人工智能" in prompt
        assert "sentiment" in prompt
        assert "topics" in prompt
        assert "relevance" in prompt
