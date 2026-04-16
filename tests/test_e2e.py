"""End-to-end tests using FastAPI TestClient."""

from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked database."""
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["tavily:url1"]],
        "documents": [["标题: Test\n正文: Content"]],
        "metadatas": [[{"channel": "tavily", "source_id": "url1", "title": "Test", "author": "", "url": "https://example.com", "published_at": "2025-06-15T10:30:00"}]],
        "distances": [[0.15]],
    }
    mock_collection.hybrid_search.return_value = mock_collection.query.return_value
    mock_collection.get.return_value = {
        "ids": [["tavily:url1"]],
        "documents": [["标题: Test\n正文: Content"]],
        "metadatas": [[{"channel": "tavily", "source_id": "url1", "title": "Test", "author": "", "url": "https://example.com", "published_at": "2025-06-15T10:30:00"}]],
    }
    mock_collection.count.return_value = 42

    with patch("src.database.init_db"), \
         patch("src.database.save_messages", return_value=1), \
         patch("src.database.get_collection", return_value=mock_collection):
        from src.main import app
        yield TestClient(app)


class TestE2E:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_list_channels(self, client):
        resp = client.get("/api/channels")
        assert resp.status_code == 200
        data = resp.json()
        names = [ch["name"] for ch in data]
        assert "tavily" in names
        assert "webhook" in names

    def test_channel_schema(self, client):
        resp = client.get("/api/channels/tavily/schema")
        assert resp.status_code == 200
        assert "properties" in resp.json()

    def test_channel_schema_not_found(self, client):
        resp = client.get("/api/channels/nonexistent/schema")
        assert resp.status_code == 404

    def test_register_channel(self, client):
        resp = client.post("/api/channels", json={"name": "tavily", "settings": {"api_key": "test-key", "query": "AI news"}})
        assert resp.status_code == 200
        assert resp.json()["name"] == "tavily"

    def test_register_unknown_channel(self, client):
        resp = client.post("/api/channels", json={"name": "unknown_channel", "settings": {}})
        assert resp.status_code == 404

    def test_semantic_search(self, client):
        resp = client.post("/api/search/semantic", json={"query": "AI 技术", "top_k": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "results" in data

    def test_hybrid_search(self, client):
        resp = client.post("/api/search/hybrid", json={"query": "AI 最新进展", "keywords": "AI", "top_k": 10})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) > 0

    def test_fulltext_search(self, client):
        resp = client.post("/api/search/fulltext", json={"query": "机器学习", "top_k": 10})
        assert resp.status_code == 200

    def test_message_count(self, client):
        resp = client.get("/api/search/messages/count")
        assert resp.status_code == 200
        assert "count" in resp.json()

    def test_webhook_receive(self, client):
        resp = client.post("/api/channels/webhook/receive", json={"title": "Test Title", "content": "Test Content"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
