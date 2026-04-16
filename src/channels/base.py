"""Abstract base class for all channel plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.channels.models import ChannelConfig, Message


class ChannelPlugin(ABC):
    """All message channels must implement this interface."""

    name: str = ""
    display_name: str = ""
    description: str = ""

    @abstractmethod
    async def fetch(self, config: ChannelConfig) -> list[Message]:
        """Fetch messages from the channel. Returns normalized Message list."""

    @abstractmethod
    def get_config_schema(self) -> dict:
        """Return JSON Schema for configuration form."""

    async def validate_config(self, config: ChannelConfig) -> bool:
        """Validate configuration (e.g. test API key)."""
        return True
