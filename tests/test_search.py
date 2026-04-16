"""Integration tests for search with seekdb."""

import pytest
import src.config
import src.database

from src.channels.models import Message


@pytest.fixture(autouse=True)
def setup_seekdb(tmp_path):
    """Use a temporary seekdb database for each test."""
    db_path = str(tmp_path / "test.db")
    src.config.settings.seekdb_db_path = db_path

    # Reset singletons
    src.database._admin = None
    src.database._client = None
    src.database._collection = None

    src.database.init_db()
    yield

    # Cleanup
    src.database._admin = None
    src.database._client = None
    src.database._collection = None


@pytest.fixture
def sample_messages():
    return [
        Message(
            channel="tavily",
            source_id="https://example.com/ai-news-1",
            title="AI breaks through in medical diagnosis",
            content="Machine learning models are now outperforming doctors in detecting early stage cancers using advanced neural networks.",
            author="Tech Reporter",
            url="https://example.com/ai-news-1",
        ),
        Message(
            channel="tavily",
            source_id="https://example.com/ai-news-2",
            title="Python remains top programming language",
            content="Python continues to dominate the AI and data science landscape with new frameworks released this year.",
            author="Dev News",
            url="https://example.com/ai-news-2",
        ),
        Message(
            channel="webhook",
            source_id="custom-001",
            title="Breaking: quantum computing milestone",
            content="Researchers achieve quantum advantage in optimization problems that could transform logistics.",
            author="Science Daily",
            url="https://example.com/quantum",
        ),
    ]


class TestSearchIntegration:
    def test_save_and_count(self, sample_messages):
        saved = src.database.save_messages(sample_messages)
        assert saved == 3
        assert src.database.get_message_count() == 3
        assert src.database.get_message_count("tavily") == 2
        assert src.database.get_message_count("webhook") == 1

    def test_semantic_search(self, sample_messages):
        src.database.save_messages(sample_messages)
        results = src.database.search_semantic("artificial intelligence medicine", n_results=5)
        assert len(results) > 0
        assert any("medical" in r["title"].lower() or "medical" in r["content"].lower() for r in results)

    def test_fulltext_search(self, sample_messages):
        src.database.save_messages(sample_messages)
        results = src.database.search_fulltext("Python", n_results=5)
        assert len(results) > 0
        assert any("Python" in r["content"] for r in results)

    def test_hybrid_search(self, sample_messages):
        src.database.save_messages(sample_messages)
        results = src.database.search_hybrid("AI technology", keywords="Python", n_results=5)
        assert len(results) > 0

    def test_search_channel_filter(self, sample_messages):
        src.database.save_messages(sample_messages)
        results = src.database.search_semantic("programming", channel="tavily", n_results=5)
        assert all(r["channel"] == "tavily" for r in results)

    def test_get_message_by_id(self, sample_messages):
        src.database.save_messages(sample_messages)
        msg = src.database.get_message_by_id("tavily:https://example.com/ai-news-1")
        assert msg is not None
        assert msg["title"] == "AI breaks through in medical diagnosis"

    def test_get_message_not_found(self):
        result = src.database.get_message_by_id("nonexistent:id")
        assert result is None

    def test_save_messages_empty_list(self):
        assert src.database.save_messages([]) == 0
