"""Vitality index computation engine."""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime

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
        evenness = 10.0
    else:
        hour_counts = Counter(hours)
        values = list(hour_counts.values())
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        evenness = max(0.0, min(20.0, 20.0 * (1 - std / max(mean, 1))))

    return round(volume + evenness, 2)


def compute_sentiment_score(analyses: list[MessageAnalysis]) -> float:
    """Sentiment score: 0-100 based on sentiment distribution."""
    if not analyses:
        return 50.0

    sentiments = [a.sentiment for a in analyses]
    avg_sentiment = sum(sentiments) / len(sentiments)
    positive_ratio = sum(1 for s in sentiments if s > 0.1) / len(sentiments)

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
