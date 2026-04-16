"""Channel management API endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.channels.models import Message
from src.channels.registry import registry
from src.database import save_messages
from src.models import ChannelCreateRequest, ChannelResponse, FetchResponse, WebhookPayload
from src.services import run_fetch, schedule_channel

router = APIRouter(prefix="/channels", tags=["channels"])

# This is set by main.py at startup
config_store: dict = {}


@router.get("", response_model=list[ChannelResponse])
def list_channels():
    results = []
    for plugin in registry.list_all():
        cfg = config_store.get(plugin.name, {})
        results.append(ChannelResponse(
            name=plugin.name, display_name=plugin.display_name,
            description=plugin.description, config_schema=plugin.get_config_schema(),
            enabled=cfg.get("enabled", True), cron=cfg.get("cron"),
            last_fetch_at=cfg.get("last_fetch_at"), last_error=cfg.get("last_error"),
            total_messages=cfg.get("total_messages", 0),
        ))
    return results


@router.get("/{name}/schema")
def get_channel_schema(name: str):
    plugin = registry.get(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Channel '{name}' not found")
    return plugin.get_config_schema()


@router.post("", response_model=ChannelResponse)
def register_channel(req: ChannelCreateRequest):
    plugin = registry.get(req.name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Channel '{req.name}' not found")

    config_store[req.name] = {"settings": req.settings, "enabled": True, "cron": req.cron}

    if req.cron:
        schedule_channel(req.name, req.cron, registry, config_store)

    cfg = config_store[req.name]
    return ChannelResponse(
        name=plugin.name, display_name=plugin.display_name,
        description=plugin.description, config_schema=plugin.get_config_schema(),
        enabled=cfg.get("enabled", True), cron=cfg.get("cron"),
    )


@router.post("/{name}/fetch", response_model=FetchResponse)
async def trigger_fetch(name: str):
    plugin = registry.get(name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Channel '{name}' not found")

    result = await run_fetch(name, registry, config_store)
    if result["success"]:
        return FetchResponse(success=True, channel=result["channel"], fetched=result.get("fetched", 0), saved=result.get("saved", 0))
    return FetchResponse(success=False, channel=name, error=result.get("error", "Unknown error"))


@router.post("/webhook/receive", response_model=FetchResponse)
async def receive_webhook(payload: WebhookPayload):
    plugin = registry.get("webhook")
    if not plugin:
        raise HTTPException(status_code=404, detail="Webhook channel not registered")

    msg = Message(
        channel="webhook", source_id=payload.source_id or payload.title,
        title=payload.title, content=payload.content, author=payload.author or "",
        url=payload.url,
        published_at=datetime.fromisoformat(payload.published_at) if payload.published_at else datetime.now(),
        metadata=payload.metadata or {},
    )
    saved = save_messages([msg])

    cfg = config_store.get("webhook", {})
    config_store["webhook"] = {
        **cfg, "last_fetch_at": datetime.now().isoformat(),
        "total_messages": cfg.get("total_messages", 0) + saved,
    }
    return FetchResponse(success=True, channel="webhook", saved=saved)
