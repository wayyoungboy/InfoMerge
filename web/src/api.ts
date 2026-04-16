const API_BASE = '/api';

export interface SearchResult {
  id: string;
  channel: string;
  title: string;
  content: string;
  author: string;
  url: string;
  published_at: string;
  score: number | null;
}

export interface SearchResponse {
  total: number;
  results: SearchResult[];
}

export interface ChannelInfo {
  name: string;
  display_name: string;
  description: string;
  config_schema: Record<string, unknown>;
  enabled: boolean;
  cron: string | null;
  last_fetch_at: string | null;
  last_error: string | null;
  total_messages: number;
}

export interface FetchResponse {
  success: boolean;
  channel: string;
  fetched: number;
  saved: number;
  error: string | null;
}

export interface VitalityResult {
  industry: string;
  total_score: number;
  activity_score: number;
  sentiment_score: number;
  diversity_score: number;
  trend_score: number;
  analyzed_at: string;
  period_start: string;
  period_end: string;
  message_count: number;
}

export interface VitalityListResponse {
  industries: VitalityResult[];
}

export interface VitalityHistoryResponse {
  industry: string;
  results: VitalityResult[];
}

export interface PaperResult {
  title: string;
  authors: string;
  abstract: string;
  url: string;
  published_at: string;
}

export interface PaperResponse {
  papers: PaperResult[];
  industry: string;
}

export async function semanticSearch(query: string, channel?: string, topK = 20): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search/semantic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, channel, top_k: topK }),
  });
  return res.json();
}

export async function hybridSearch(query: string, keywords?: string, channel?: string, topK = 20): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search/hybrid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, keywords, channel, top_k: topK }),
  });
  return res.json();
}

export async function listChannels(): Promise<ChannelInfo[]> {
  const res = await fetch(`${API_BASE}/channels`);
  return res.json();
}

export async function triggerFetch(channelName: string): Promise<FetchResponse> {
  const res = await fetch(`${API_BASE}/channels/${channelName}/fetch`, {
    method: 'POST',
  });
  return res.json();
}

export async function registerChannel(name: string, settings: Record<string, unknown>, cron?: string): Promise<ChannelInfo> {
  const res = await fetch(`${API_BASE}/channels`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, settings, cron }),
  });
  return res.json();
}

export async function getChannelSchema(name: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/channels/${name}/schema`);
  return res.json();
}

export async function analyzeVitality(
  industry: string,
  periodDays = 7,
  maxMessages = 100
): Promise<VitalityResult | { error: string }> {
  const res = await fetch(`${API_BASE}/vitality/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ industry, period_days: periodDays, max_messages: maxMessages }),
  });
  return res.json();
}

export async function listVitalality(): Promise<VitalityListResponse> {
  const res = await fetch(`${API_BASE}/vitality/list`);
  return res.json();
}

export async function getVitalityHistory(industry: string): Promise<VitalityHistoryResponse> {
  const res = await fetch(`${API_BASE}/vitality/history/${industry}`);
  return res.json();
}

export async function searchPapers(industry: string): Promise<PaperResponse> {
  const res = await fetch(`${API_BASE}/vitality/papers/${industry}`);
  return res.json();
}

export async function discoverIndustries(): Promise<{ industries: Array<{ industry: string; message_count: number }> }> {
  const res = await fetch(`${API_BASE}/vitality/discover`, {
    method: 'POST',
  });
  return res.json();
}
