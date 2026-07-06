# /literature — Academic Literature Trend Analyzer

A Claude Code skill for analyzing research trends in academic topics. Collects data from 5 free academic APIs and produces structured trend analysis reports with evidence chains.

**An AI agent-led research trend analyzer scored by citations, publications, and benchmark results.**

```
/literature few-shot image classification
/literature vision transformer --categories cs.CV cs.LG --years 2023 2026
/literature domain adaptation --competitors
```

## Features

- **Parallel data collection** — Fetches from 5 sources simultaneously (arXiv, Semantic Scholar, CrossRef, Papers With Code, DBLP)
- **Method classification** — Automatically categorizes papers by method type (meta-learning, transformer-based, foundation model, prompt tuning, etc.)
- **Trend detection** — Identifies growing/declining directions, benchmark saturation, and citation trends
- **Evidence chains** — Every conclusion is backed by specific numbers, paper lists, and confidence levels
- **Auditable** — All raw data saved locally for verification

## Quick Start

### Claude Code (recommended)

**Coming soon to plugin marketplace.** Install via agent-skills:

```bash
npx skills add zhaoweihua001/literature-trends -g
```

Then in Claude Code:

```
/literature few-shot image classification
```

### Manual Install (for development)

1. Clone the repo and install dependencies:

```bash
git clone https://github.com/zhaoweihua001/literature-trends.git
cd literature-trends
pip install -r requirements.txt
```

2. Run the engine directly:

```bash
python scripts/engine.py --topic "few-shot image classification" \
  --categories cs.CV --years 2024 2026 --max-results 50
```

The engine outputs JSON to stdout. Claude Code's SKILL.md handles the analysis layer.

## Data Sources

| Source | Provides | Auth | Rate Limit |
|--------|----------|------|------------|
| **arXiv API** | Paper titles, abstracts, authors, categories | None | 1 req/3s |
| **Semantic Scholar** | Citation counts, influential citations, paper URLs | Free API key (optional) | 100 req/min |
| **CrossRef** | Journal/publisher info, DOI metadata | None (use mailto) | 50 req/s |
| **Papers With Code** | Benchmark rankings, SOTA trends, code links | None | Unrestricted |
| **DBLP** | Conference/journal publication statistics | None | 1 req/s |

## Method Categories

The engine classifies papers into these categories based on keyword matching in titles and abstracts:

`foundation_model` · `transformer_based` · `meta_learning` · `prompt_tuning` · `data_augmentation` · `transfer_learning` · `generative` · `graph_neural_network` · `metric_learning` · `ensemble` · `other`

## Output

Running the engine produces a structured JSON with:

- `meta` — query parameters, source statistics
- `papers` — full list with enrichment from all sources
- `method_categories` — count, avg citation, trend per category
- `yearly_stats` — paper counts and citations by year
- `keyword_trends` — frequency of tracked keywords over time
- `benchmark_trends` — SOTA progression on tracked datasets
- `high_impact_papers` — top papers by citation count
- `venue_distribution` — publication venue statistics

Claude Code (via SKILL.md) reads this JSON and produces a human-readable trend report.

## Requirements

- Python 3.12+
- `requests` library

## Project Structure

```
literature-trends/
├── SKILL.md               # Skill entry point for Claude Code
├── scripts/
│   └── engine.py          # Main orchestrator
├── engine/
│   ├── fetchers/          # API wrappers (5 sources)
│   ├── merge.py           # Dedup + enrichment merger
│   ├── classify.py        # Method classification rules
│   └── output.py          # JSON output assembler
└── tests/                 # 23 tests
```

## License

MIT

---

## 🇨🇳 中文说明

# /literature — 学术文献趋势分析 Skill

一个 Claude Code 技能，帮助研究生/博士生分析任意学术课题的研究趋势。同时从 5 个免费学术 API 获取数据，产出带证据链的结构化趋势分析报告。

```
/literature few-shot image classification
/literature vision transformer --categories cs.CV cs.LG --years 2023 2026
/literature 少样本图像分类
```

### 它能回答什么问题？

- **这个课题近 3 年大家都在做什么方向？** — 按方法分类统计（meta-learning、transformer、foundation model 等）
- **哪个方向在增长、哪个在饱和？** — 论文量趋势 + 引用增长曲线 + benchmark SOTA 变化
- **我现在做这个方向还有空间吗？** — 基于竞争程度和引用表现给出建议
- **高引论文在做什么？** — TOP 10 高影响力论文及其共同点

### 数据源

| 来源 | 提供数据 | 费用 |
|------|---------|------|
| **arXiv** | 论文标题、摘要、作者、分类 | 免费 |
| **Semantic Scholar** | 引用数、高影响力引用 | 免费（可选 API Key） |
| **CrossRef** | 期刊/出版社信息、DOI | 免费 |
| **Papers With Code** | Benchmark 排行榜、SOTA 趋势 | 免费 |
| **DBLP** | 会议/期刊收录统计 | 免费 |

### 安装方式

**Claude Code 用户：**
```
/plugin marketplace add zhaoweihua001/literature-trends
```

**跨平台（Codex、Cursor、Gemini CLI 等）：**
```bash
npx skills add zhaoweihua001/literature-trends -g
```

**使用：**
```
/literature 少样本图像分类
/literature vision transformer --years 2023 2026 --max-results 200
```

### 快速本地运行（不需要 Claude Code）

```bash
pip install requests
python scripts/engine.py --topic "few-shot image classification" \
  --categories cs.CV --years 2024 2026 --max-results 50
```

引擎会输出结构化 JSON 到 stdout。

### 方法分类

引擎根据标题和摘要中的关键词，将论文自动分类为：

`foundation_model`（基石模型） · `transformer_based`（Transformer） · `meta_learning`（元学习） · `prompt_tuning`（提示调优） · `data_augmentation`（数据增强） · `transfer_learning`（迁移学习） · `generative`（生成式） · `graph_neural_network`（图神经网络） · `metric_learning`（度量学习） · `ensemble`（集成） · `other`（其他）

### 项目结构

```
literature-trends/
├── SKILL.md               # Skill 入口（Claude Code 读取）
├── scripts/
│   └── engine.py          # 主编排器
├── engine/
│   ├── fetchers/          # 5 个数据源 API 封装
│   ├── merge.py           # 去重 + 合并
│   ├── classify.py        # 方法分类
│   └── output.py          # JSON 输出组装
└── tests/                 # 23 个测试
```
