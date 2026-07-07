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
