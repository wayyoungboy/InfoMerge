# 行业活力指数分析 — 设计文档

## 概述

在 InfoMerge 平台上新增「行业活力指数」分析功能，通过 LLM 对采集的消息进行多维度分析，计算行业活力指数并可视化展示。

## 架构

```
用户访问 /vitality 页面
  → Frontend: VitalityPage（新页面）
    → Backend: FastAPI 新增 /api/vitality/* 路由
      ├── seekdb（消息检索，按行业关键词 + 时间窗口）
      ├── LLM Provider（情感分析、话题聚类、行业分类）
      ├── SQLite（分析结果持久化、时序历史）
      └── 论文搜索 MCP（ModelScope paper-search-mcp）
```

## 核心模块

### 1. LLM Provider 接口

**文件**: `src/analysis/llm_provider.py`

```python
class MessageAnalysis:
    sentiment: float          # -1.0 ~ 1.0
    topics: list[str]         # 1-3 个话题标签
    relevance: float          # 0.0 ~ 1.0，行业相关度

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_messages(self, messages: list[dict]) -> list[MessageAnalysis]: ...
```

实现 `OpenAIProvider`（通过 OpenAI 兼容 API），配置项：
- `llm_api_base`: API base URL（如 `https://api.openai.com/v1`）
- `llm_api_key`: API key
- `llm_model`: 模型名（如 `gpt-4o-mini`）

**System prompt**: 要求 LLM 以 JSON 数组返回每条消息的 sentiment、topics、relevance。
**批处理**: 每批 20 条消息，避免单次请求过大。

### 2. 行业发现

**文件**: `src/analysis/discoverer.py`

- 从 seekdb 拉取最近 N 条消息，调用 LLM 做行业分类
- LLM 返回行业列表 + 消息数量统计
- 结果存入 `config_store` 作为推荐行业列表
- 可通过 `POST /api/vitality/discover` 手动触发

### 3. 指数计算引擎

**文件**: `src/analysis/engine.py`

4 个维度（各 0-100 分）：

| 维度 | 权重 | 计算逻辑 |
|------|------|----------|
| 活跃度 | 30% | 消息数（归一化到 0-80）+ 时间均匀度（标准差倒数，0-20） |
| 情感倾向 | 25% | (正面占比×100 + avg_sentiment×50 + 100) / 2 |
| 话题多样性 | 20% | min(独立话题数 / 10, 1.0) × 100 |
| 时间趋势 | 25% | ((本期-上期)/max(上期,1)) 映射到 0-100（sigmoid 平滑） |

总指数 = Σ(维度 × 权重)

### 4. 数据持久化

**文件**: `src/analysis/store.py`

SQLite 数据库 `data/vitality.db`：

```sql
CREATE TABLE vitality_results (
    id INTEGER PRIMARY KEY,
    industry TEXT NOT NULL,
    total_score REAL,
    activity_score REAL,
    sentiment_score REAL,
    diversity_score REAL,
    trend_score REAL,
    analyzed_at TEXT,
    period_start TEXT,
    period_end TEXT,
    message_count INTEGER
);

CREATE TABLE discovered_industries (
    id INTEGER PRIMARY KEY,
    industry TEXT NOT NULL UNIQUE,
    message_count INTEGER,
    discovered_at TEXT
);
```

### 5. API 路由

**文件**: `src/api/vitality.py`

| Method | Path | 功能 |
|--------|------|------|
| `POST` | `/api/vitality/analyze` | 触发行业分析，参数: `industry`(关键词), `period_days`(默认7), 返回指数 |
| `GET` | `/api/vitality/list` | 已分析行业列表 + 最新指数 |
| `GET` | `/api/vitality/history/{industry}` | 行业历史时序数据 |
| `GET` | `/api/vitality/papers/{industry}` | 论文搜索结果 |
| `POST` | `/api/vitality/discover` | 触发 LLM 行业发现 |

### 6. 配置

**文件**: `src/config.py`（扩展）

```python
llm_api_base: str = ""
llm_api_key: str = ""
llm_model: str = "gpt-4o-mini"
```

**.env.example** 新增对应字段。

### 7. 前端页面

**文件**: `web/src/pages/VitalityPage.tsx`

- **顶部**: 行业搜索输入框 + "分析" 按钮 + "自动发现" 按钮
- **指数卡片网格**: 每个已分析行业一张卡片，显示行业名、总指数（大号数字）、4 维度迷你进度条、趋势箭头（↑↓→ 对比上期）
- **论文搜索区**: 在卡片下方，显示最近论文搜索结果

路由: `web/src/App.tsx` 新增 `/vitality` 路由。

API 客户端: `web/src/api.ts` 新增 `analyzeVitality()`, `listVitalality()`, `getVitalityHistory()`, `searchPapers()`, `discoverIndustries()`。

## 数据流

1. 用户输入行业关键词 → POST /api/vitality/analyze
2. 后端从 seekdb 拉取该行业匹配的最近消息（按 period_days）
3. LLM 批量分析每条消息（sentiment、topics、relevance）
4. 分析结果存入 seekdb metadata + SQLite vitality_results
5. 引擎计算 4 维度分数 + 总指数
6. 取上期数据做趋势对比
7. 返回结果给前端渲染

## 错误处理

- LLM API 不可用: 返回 502，前端提示 "LLM 服务不可用，请检查配置"
- seekdb 无数据: 返回空结果，前端提示 "未找到相关行业消息"
- 论文搜索失败: 降级为空列表，不影响指数展示
- 指数计算无上期数据: trend_score 设为 50（中性）

## 测试

- `tests/test_analysis/` 目录
- `test_llm_provider.py`: 模拟 LLM 响应，验证消息格式化和结果解析
- `test_engine.py`: 给定分析数据，验证 4 维度计算正确性
- `test_store.py`: SQLite CRUD 操作
- `test_vitality_api.py`: E2E 测试，模拟 LLM 响应，验证完整分析流程

## 文件变更清单

**新建**:
- `src/analysis/__init__.py`
- `src/analysis/llm_provider.py`
- `src/analysis/discoverer.py`
- `src/analysis/engine.py`
- `src/analysis/store.py`
- `src/api/vitality.py`
- `web/src/pages/VitalityPage.tsx`
- `tests/test_analysis/test_llm_provider.py`
- `tests/test_analysis/test_engine.py`
- `tests/test_analysis/test_store.py`
- `tests/test_vitality_api.py`

**修改**:
- `src/config.py` — 新增 LLM 配置
- `.env.example` — 新增 LLM 字段模板
- `src/main.py` — 注册 vitality router
- `src/models.py` — 新增 Pydantic 请求/响应模型
- `web/src/api.ts` — 新增 vitality API 函数
- `web/src/App.tsx` — 新增 /vitality 路由和导航链接
