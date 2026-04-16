"""Collection orchestration service."""

from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.channels.models import ChannelConfig
from src.channels.registry import ChannelRegistry
from src.database import save_messages

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_fetch(channel_name: str, registry: ChannelRegistry, config_store: dict) -> dict:
    """Execute a single fetch cycle for a channel."""
    plugin = registry.get(channel_name)
    if not plugin:
        return {"success": False, "error": f"Channel '{channel_name}' not found"}

    config_data = config_store.get(channel_name, {})
    config = ChannelConfig.from_dict({"channel_name": channel_name, **config_data})

    if not config.enabled:
        return {"success": False, "error": "Channel is disabled"}

    try:
        messages = await plugin.fetch(config)
        saved = save_messages(messages)

        config_store[channel_name] = {
            **config_data,
            "last_fetch_at": datetime.now().isoformat(),
            "total_messages": config_data.get("total_messages", 0) + saved,
            "last_error": None,
        }

        return {"success": True, "fetched": len(messages), "saved": saved, "channel": channel_name}
    except Exception as e:
        logger.exception(f"Fetch failed for {channel_name}")
        config_store[channel_name] = {**config_data, "last_error": str(e)}
        return {"success": False, "error": str(e)}


def schedule_channel(channel_name: str, cron: str, registry: ChannelRegistry, config_store: dict) -> None:
    """Schedule periodic fetch for a channel."""
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        run_fetch, CronTrigger.from_crontab(cron),
        args=[channel_name, registry, config_store],
        id=f"fetch_{channel_name}", replace_existing=True,
    )


def unschedule_channel(channel_name: str) -> None:
    """Remove scheduled fetch for a channel."""
    try:
        scheduler.remove_job(f"fetch_{channel_name}")
    except Exception:
        pass
