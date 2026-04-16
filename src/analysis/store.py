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
