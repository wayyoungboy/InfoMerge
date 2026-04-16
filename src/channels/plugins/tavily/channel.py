"""Tavily news search channel plugin."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from tavily import TavilyClient

from src.channels.base import ChannelPlugin
from src.channels.models import Message

if TYPE_CHECKING:
    from src.channels.models import ChannelConfig


class TavilyChannel(ChannelPlugin):
    """Tavily web search for news and articles."""

    name = "tavily"
    display_name = "Tavily 新闻搜索"
    description = "通过 Tavily API 搜索新闻和文章"

    async def fetch(self, config: ChannelConfig) -> list[Message]:
        api_key = config.settings["api_key"]
        query = config.settings.get("query", "tech news")
        max_results = int(config.settings.get("max_results", 10))
        topic = config.settings.get("topic", "news")

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            topic=topic,
        )

        messages = []
        for result in response.get("results", []):
            messages.append(
                Message(
                    channel=self.name,
                    source_id=result["url"],
                    title=result.get("title", ""),
                    content=result.get("content", ""),
                    url=result["url"],
                    published_at=datetime.now(),
                )
            )
        return messages

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["api_key"],
            "properties": {
                "api_key": {"type": "string", "title": "API Key", "format": "password"},
                "query": {"type": "string", "title": "搜索关键词", "default": "tech news"},
                "max_results": {"type": "integer", "title": "每次采集数量", "default": 10, "minimum": 1, "maximum": 20},
                "topic": {"type": "string", "title": "搜索类型", "default": "news", "enum": ["general", "news"]},
            },
        }

    async def validate_config(self, config: ChannelConfig) -> bool:
        api_key = config.settings.get("api_key", "")
        if not api_key:
            return False
        try:
            client = TavilyClient(api_key=api_key)
            client.search(query="test", max_results=1)
            return True
        except Exception:
            return False


# Register plugin when module is imported
from src.channels.registry import registry

registry.register(TavilyChannel())
