"""Tests for TavilyChannel (mocked API)."""

import pytest
from src.channels.models import ChannelConfig
from src.channels.plugins.tavily.channel import TavilyChannel


class TestTavilyChannel:
    def test_config_schema(self):
        plugin = TavilyChannel()
        schema = plugin.get_config_schema()
        assert schema["type"] == "object"
        assert "api_key" in schema["required"]
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]

    def test_plugin_attributes(self):
        plugin = TavilyChannel()
        assert plugin.name == "tavily"
        assert plugin.display_name == "Tavily 新闻搜索"

    @pytest.mark.asyncio
    async def test_validate_config_empty(self):
        plugin = TavilyChannel()
        config = ChannelConfig(channel_name="tavily", settings={"api_key": ""})
        assert await plugin.validate_config(config) is False

    @pytest.mark.asyncio
    async def test_validate_config_missing_key(self):
        plugin = TavilyChannel()
        config = ChannelConfig(channel_name="tavily", settings={})
        assert await plugin.validate_config(config) is False
