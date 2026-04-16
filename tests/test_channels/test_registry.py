"""Tests for ChannelRegistry."""

from src.channels.base import ChannelPlugin
from src.channels.models import ChannelConfig, Message
from src.channels.registry import ChannelRegistry


class FakeChannel(ChannelPlugin):
    name = "fake"
    display_name = "Fake Channel"
    description = "A fake channel for testing"

    async def fetch(self, config: ChannelConfig) -> list[Message]:
        return []

    def get_config_schema(self) -> dict:
        return {"type": "object", "properties": {}}


class TestChannelRegistry:
    def test_register_and_get(self):
        registry = ChannelRegistry()
        plugin = FakeChannel()
        registry.register(plugin)
        assert registry.get("fake") is plugin

    def test_get_unknown(self):
        registry = ChannelRegistry()
        assert registry.get("unknown") is None

    def test_list_all(self):
        registry = ChannelRegistry()
        registry.register(FakeChannel())
        plugins = registry.list_all()
        assert len(plugins) == 1
        assert plugins[0].name == "fake"

    def test_register_overwrites(self):
        registry = ChannelRegistry()
        registry.register(FakeChannel())
        new_plugin = FakeChannel()
        registry.register(new_plugin)
        assert registry.get("fake") is new_plugin
