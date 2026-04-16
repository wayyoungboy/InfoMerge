"""Tests for vitality index computation engine."""

from src.analysis.engine import (
    compute_activity_score,
    compute_sentiment_score,
    compute_diversity_score,
    compute_trend_score,
    compute_vitality_index,
)
from src.analysis.llm_provider import MessageAnalysis


class TestActivityScore:
    def test_zero_messages(self):
        assert compute_activity_score(0, []) == 0.0

    def test_high_volume_even_distribution(self):
        timestamps = [f"2026-04-17T{i:02d}:00:00" for i in range(10)]
        score = compute_activity_score(10, timestamps)
        assert 60 <= score <= 100

    def test_clustered_distribution(self):
        timestamps = ["2026-04-17T10:00:00"] * 5
        score = compute_activity_score(5, timestamps)
        assert score < 60


class TestSentimentScore:
    def test_all_positive(self):
        scores = compute_sentiment_score([
            MessageAnalysis(0.8, [], 1),
            MessageAnalysis(0.9, [], 1),
            MessageAnalysis(0.7, [], 1),
        ])
        assert scores > 80

    def test_all_negative(self):
        scores = compute_sentiment_score([
            MessageAnalysis(-0.8, [], 1),
            MessageAnalysis(-0.9, [], 1),
            MessageAnalysis(-0.7, [], 1),
        ])
        assert scores <= 30

    def test_neutral(self):
        scores = compute_sentiment_score([
            MessageAnalysis(0.0, [], 1),
            MessageAnalysis(0.0, [], 1),
            MessageAnalysis(0.0, [], 1),
        ])
        assert 40 <= scores <= 60

    def test_empty(self):
        assert compute_sentiment_score([]) == 50.0


class TestDiversityScore:
    def test_many_topics(self):
        topics = ["AI", "医疗", "监管", "投资", "人才", "政策", "技术", "市场"]
        assert compute_diversity_score(topics) == 80.0

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
