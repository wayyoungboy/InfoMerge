"""Pydantic models for API request/response."""

from pydantic import BaseModel, Field
from typing import Optional


class ChannelCreateRequest(BaseModel):
    name: str = Field(..., description="Channel plugin name (e.g. 'tavily')")
    settings: dict = Field(default_factory=dict, description="Channel-specific settings")
    cron: Optional[str] = Field(None, description="Cron expression for scheduled fetch")


class ChannelResponse(BaseModel):
    name: str
    display_name: str
    description: str
    config_schema: dict
    enabled: bool = True
    cron: Optional[str] = None
    last_fetch_at: Optional[str] = None
    last_error: Optional[str] = None
    total_messages: int = 0


class FetchResponse(BaseModel):
    success: bool
    channel: str
    fetched: int = 0
    saved: int = 0
    error: Optional[str] = None


class WebhookPayload(BaseModel):
    title: str
    content: str
    author: Optional[str] = ""
    url: Optional[str] = None
    source_id: Optional[str] = None
    published_at: Optional[str] = None
    metadata: Optional[dict] = None


class SearchResult(BaseModel):
    id: str
    channel: str
    title: str
    content: str
    author: str
    url: str
    published_at: str
    score: Optional[float] = None


class SearchResponse(BaseModel):
    total: int
    results: list[SearchResult]


class SemanticSearchRequest(BaseModel):
    query: str
    channel: Optional[str] = None
    top_k: int = 20


class FulltextSearchRequest(BaseModel):
    query: str
    channel: Optional[str] = None
    top_k: int = 20


class HybridSearchRequest(BaseModel):
    query: str
    keywords: Optional[str] = None
    channel: Optional[str] = None
    top_k: int = 20


class VitalityResult(BaseModel):
    industry: str
    total_score: float
    activity_score: float
    sentiment_score: float
    diversity_score: float
    trend_score: float
    analyzed_at: str
    period_start: str
    period_end: str
    message_count: int


class VitalityAnalyzeRequest(BaseModel):
    industry: str = Field(..., description="Industry keyword")
    period_days: int = Field(default=7, ge=1, le=90)
    max_messages: int = Field(default=100, ge=1, le=1000)


class VitalityListResponse(BaseModel):
    industries: list[VitalityResult]


class PaperResult(BaseModel):
    title: str
    authors: str
    abstract: str
    url: str
    published_at: str


class VitalityHistoryResponse(BaseModel):
    industry: str
    results: list[VitalityResult]
