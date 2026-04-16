"""Shared pytest fixtures."""

import pytest
from datetime import datetime
from src.channels.models import ChannelConfig, Message


@pytest.fixture
def sample_message():
    return Message(
        channel="tavily",
        source_id="https://example.com/test",
        title="Test Article",
        content="This is test content about AI and machine learning.",
        author="Test Author",
        published_at=datetime(2025, 6, 15, 10, 30, 0),
        url="https://example.com/test",
    )


@pytest.fixture
def sample_config():
    return ChannelConfig(
        channel_name="tavily",
        settings={"api_key": "test-key", "query": "tech news"},
        enabled=True,
        cron="*/30 * * * *",
    )
