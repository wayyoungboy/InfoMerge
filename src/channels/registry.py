"""Channel plugin registry."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.channels.base import ChannelPlugin


class ChannelRegistry:
    """Register and discover channel plugins."""

    def __init__(self):
        self._plugins: dict[str, ChannelPlugin] = {}

    def register(self, plugin: ChannelPlugin) -> None:
        """Register a channel plugin."""
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> ChannelPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def list_all(self) -> list[ChannelPlugin]:
        """List all registered plugins."""
        return list(self._plugins.values())

    def auto_discover(self, plugin_dir: Path) -> None:
        """Scan plugin directory and register all plugins found."""
        if not plugin_dir.is_dir():
            return
        for item in sorted(plugin_dir.iterdir()):
            if item.is_dir() and (item / "__init__.py").exists():
                rel = item.relative_to(plugin_dir.parent)
                module_path = ".".join(rel.parts)
                import_module(module_path)


# Global singleton
registry = ChannelRegistry()
