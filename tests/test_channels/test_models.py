"""Tests for Message and ChannelConfig models."""

from datetime import datetime
from src.channels.models import ChannelConfig, Message


class TestMessage:
    def test_doc_id(self, sample_message):
        assert sample_message.doc_id() == "tavily:https://example.com/test"

    def test_to_document(self, sample_message):
        doc = sample_message.to_document()
        assert "标题: Test Article" in doc
        assert "正文: This is test content" in doc

    def test_to_metadata(self, sample_message):
        meta = sample_message.to_metadata()
        assert meta["channel"] == "tavily"
        assert meta["source_id"] == "https://example.com/test"
        assert meta["title"] == "Test Article"
        assert meta["author"] == "Test Author"
        assert meta["url"] == "https://example.com/test"
        assert meta["published_at"] == "2025-06-15T10:30:00"

    def test_to_metadata_missing_url(self):
        msg = Message(
            channel="webhook",
            source_id="123",
            title="No URL",
            content="content",
        )
        meta = msg.to_metadata()
        assert meta["url"] == ""

    def test_default_values(self):
        msg = Message(
            channel="test",
            source_id="1",
            title="T",
            content="C",
        )
        assert msg.author == ""
        assert msg.published_at is None
        assert msg.url is None
        assert msg.metadata == {}


class TestChannelConfig:
    def test_to_dict(self, sample_config):
        d = sample_config.to_dict()
        assert d["channel_name"] == "tavily"
        assert d["settings"]["api_key"] == "test-key"
        assert d["enabled"] is True
        assert d["cron"] == "*/30 * * * *"

    def test_from_dict(self):
        data = {
            "channel_name": "tavily",
            "settings": {"api_key": "key"},
            "enabled": False,
            "cron": None,
            "last_fetch_at": "2025-06-15T10:30:00",
            "last_error": "timeout",
            "total_messages": 42,
        }
        config = ChannelConfig.from_dict(data)
        assert config.channel_name == "tavily"
        assert config.enabled is False
        assert config.cron is None
        assert config.last_fetch_at == datetime(2025, 6, 15, 10, 30, 0)
        assert config.last_error == "timeout"
        assert config.total_messages == 42

    def test_roundtrip(self, sample_config):
        data = sample_config.to_dict()
        restored = ChannelConfig.from_dict(data)
        assert restored.channel_name == sample_config.channel_name
        assert restored.settings == sample_config.settings
        assert restored.enabled == sample_config.enabled
