"""FastAPI application entry point."""

import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.channels.plugins.tavily.channel import TavilyChannel  # noqa: F401
from src.channels.plugins.webhook.channel import WebhookChannel  # noqa: F401
from src.channels.registry import registry
from src.database import init_db
from src.services import scheduler
from src.analysis.store import VitalityStore

config_store: dict = {}
vitality_store = VitalityStore("./data/vitality.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    init_db()

    plugins_dir = pathlib.Path(__file__).parent / "channels" / "plugins"
    registry.auto_discover(plugins_dir)

    scheduler.start()
    yield
    scheduler.shutdown()
    vitality_store.close()


app = FastAPI(title="InfoMerge", description="Multi-source hot topic collection and analysis platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

import src.api.channels as channels_module
channels_module.config_store = config_store

from src.api.channels import router as channels_router
from src.api.search import router as search_router
from src.api.vitality import router as vitality_router, set_store

app.include_router(channels_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(vitality_router, prefix="/api")

set_store(vitality_store)


@app.get("/api/health")
def health():
    return {"status": "ok"}
