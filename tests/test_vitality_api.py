"""E2E tests for vitality API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client with mocked DB and empty vitality store."""
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


class TestVitalityAPI:
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
        assert res.status_code in (400, 422)

    def test_papers_empty(self, client):
        res = client.get("/api/vitality/papers/test")
        assert res.status_code == 200
        assert res.json()["papers"] == []

    def test_discover_no_llm_config(self, client):
        res = client.post("/api/vitality/discover")
        assert res.status_code in (400, 422)
