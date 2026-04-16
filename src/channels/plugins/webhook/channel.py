"""Webhook channel - receives messages via HTTP POST."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.channels.base import ChannelPlugin
from src.channels.models import Message

if TYPE_CHECKING:
    from src.channels.models import ChannelConfig


class WebhookChannel(ChannelPlugin):
    """Receives messages from external sources via webhook POST."""

    name = "webhook"
    display_name = "自定义 Webhook"
    description = "通过 HTTP POST 接收外部系统的消息"

    async def fetch(self, config: ChannelConfig) -> list[Message]:
        return []

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "required": [],
            "properties": {
                "webhook_secret": {"type": "string", "title": "Webhook 密钥 (可选)", "format": "password", "default": ""},
            },
        }


from src.channels.registry import registry

registry.register(WebhookChannel())
