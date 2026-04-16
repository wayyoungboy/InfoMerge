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
        s.close()  # double close should be safe
