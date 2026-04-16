"""Channel and message data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """Standardized message from any channel."""

    channel: str
    source_id: str
    title: str
    content: str
    author: str = ""
    published_at: Optional[datetime] = None
    url: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_document(self) -> str:
        """Convert to seekdb document string."""
        return f"标题: {self.title}\n正文: {self.content}"

    def to_metadata(self) -> dict:
        """Convert to seekdb metadata dict."""
        meta = {
            "channel": self.channel,
            "source_id": self.source_id,
            "title": self.title,
            "author": self.author,
            "url": self.url or "",
            "published_at": self.published_at.isoformat() if self.published_at else "",
        }
        meta.update(self.metadata)
        return meta

    def doc_id(self) -> str:
        """Unique document ID for seekdb."""
        return f"{self.channel}:{self.source_id}"


@dataclass
class ChannelConfig:
    """Configuration for a registered channel."""

    channel_name: str
    settings: dict = field(default_factory=dict)
    enabled: bool = True
    cron: Optional[str] = None
    last_fetch_at: Optional[datetime] = None
    last_error: Optional[str] = None
    total_messages: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ChannelConfig:
        """Create from JSON-compatible dict."""
        return cls(
            channel_name=data["channel_name"],
            settings=data.get("settings", {}),
            enabled=data.get("enabled", True),
            cron=data.get("cron"),
            last_fetch_at=(
                datetime.fromisoformat(data["last_fetch_at"])
                if data.get("last_fetch_at")
                else None
            ),
            last_error=data.get("last_error"),
            total_messages=data.get("total_messages", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "channel_name": self.channel_name,
            "settings": self.settings,
            "enabled": self.enabled,
            "cron": self.cron,
            "last_fetch_at": (
                self.last_fetch_at.isoformat() if self.last_fetch_at else None
            ),
            "last_error": self.last_error,
            "total_messages": self.total_messages,
        }
