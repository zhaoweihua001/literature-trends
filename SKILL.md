---
name: literature
version: "1.0.0"
description: "Analyze academic research trends for any topic. Collects papers from arXiv, Semantic Scholar, CrossRef, Papers With Code, and DBLP, then produces a structured trend analysis report with evidence chains — method trends, citation analysis, benchmark saturation, and direction suggestions."
argument-hint: 'literature few-shot image classification | literature vision transformer --years 2023 2026 | literature domain adaptation'
allowed-tools: Bash, Read, Write
homepage: https://github.com/zhaoweihua001/literature-trends
repository: https://github.com/zhaoweihua001/literature-trends
author: zhaoweihua001
license: MIT
user-invocable: true
metadata:
  openclaw:
    emoji: "📚"
    requires:
      - python: ">=3.12"
---

# /literature — Academic Literature Trend Analyzer

Analyze research trends for any academic topic. Collects data from arXiv, Semantic Scholar, CrossRef, Papers With Code, and DBLP, then produces a trend analysis report with evidence chains.

**Note:** This skill uses a Python engine (requires Python 3.12+). The engine outputs structured JSON which Claude then analyzes for trends and suggestions.

## Usage

```
/literature <topic> [--categories <cats>] [--years <start> <end>] [--max-results <N>]
/literature --doctor    (diagnose all data sources)
```

**Examples:**
- `/literature few-shot image classification`
- `/literature vision transformer --categories cs.CV cs.LG`
- `/literature domain adaptation --years 2023 2026 --max-results 300`
- `/literature --doctor`

## Runtime Preflight

Before running the engine, resolve a Python 3.12+ interpreter:

```bash
try_literature_python() {
  candidate="$1"
  [ -n "$candidate" ] || return 1
  if [ -x "$candidate" ]; then :
  elif command -v "$candidate" >/dev/null 2>&1; then :
  else return 1
  fi
  "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || return 1
  LITERATURE_PYTHON="$candidate"
  return 0
}

LITERATURE_PYTHON=""
for py in python3.14 python3.13 python3.12 python3 python; do
  try_literature_python "$py" && break
done

if [ -z "${LITERATURE_PYTHON:-}" ]; then
  echo "ERROR: literature skill requires Python 3.12+. Install Python 3.12+ first." >&2
  exit 1
fi

LITERATURE_MEMORY_DIR="${LITERATURE_MEMORY_DIR:-$HOME/Documents/AcademicTrends}"
mkdir -p "$LITERATURE_MEMORY_DIR"
```

## Step 1: Parse User Intent

If the user's input is `--doctor`, skip research and run the diagnostic instead (see Step 2b below).

Otherwise, extract from the user's command:
- **TOPIC**: the research topic to analyze
- **CATEGORIES**: arXiv categories (default: cs.CV)
- **YEARS**: year range (default: last 3 years)
- **MAX_RESULTS**: max papers to fetch (default: 100)

## Step 2: Run the Engine

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
if [ ! -f "$SKILL_DIR/scripts/engine.py" ]; then
  echo "ERROR: scripts/engine.py not found under SKILL_DIR=$SKILL_DIR" >&2
  exit 1
fi

SAVE_DIR="${LITERATURE_MEMORY_DIR}/${TOPIC_SLUG}-$(date +%Y-%m-%d)"
mkdir -p "$SAVE_DIR"

"${LITERATURE_PYTHON}" "${SKILL_DIR}/scripts/engine.py" \
  --topic "$TOPIC" \
  --categories ${CATEGORIES} \
  --years ${START_YEAR} ${END_YEAR} \
  --max-results ${MAX_RESULTS} \
  --save-dir "$SAVE_DIR" \
  2>/dev/null
```

### If TOPIC is --doctor, run this instead:

```bash
SKILL_DIR="<absolute path of the directory containing this SKILL.md>"
"${LITERATURE_PYTHON}" "${SKILL_DIR}/scripts/engine.py" --doctor 2>/dev/null
```

Display the diagnostic results (see Step 3 Doctor Mode below).

## Step 3: Claude Analyzes the JSON Output

Read the JSON output and produce a trend report with:
1. **Overview** — total papers, sources, date range
2. **Method Distribution** — what categories are people working on?
3. **Trend Highlights** — which directions are growing/declining?
4. **Citation Analysis** — high-impact papers and what they have in common
5. **Benchmark Status** — which datasets are saturated?
6. **Suggestions** — where might there be room to contribute?

Each insight must include:
- **Evidence**: specific numbers, paper counts, citations
- **Confidence**: 🟢 high / 🟡 medium / 🔴 low
- **Traceability**: which data source and which papers support this

## Step 4: Invite Follow-up Questions

Offer to dive deeper into specific sub-directions, compare categories, or explore specific papers.

---

## Step 3: Doctor Mode (when --doctor was used)

Read the JSON diagnostic output and format it as a human-readable health check:

```markdown
📋 数据源健康检查：
├─ 🟢 Python: 3.12.10
├─ 🟢 arXiv API: Connected
├─ 🟡 Semantic Scholar: Rate limited
│   └─ 修复：申请免费 API Key → https://www.semanticscholar.org/product/api
├─ 🔴 DBLP: HTTP 500（临时故障）
└─ 🟢 CCF Rankings: OK

Summary: 6/9 🟢 | 1/9 🟡 | 2/9 🔴
```

Highlight sources that need attention and offer to help fix them.

---

## Security & Permissions

- Sends queries to: arXiv API (public), Semantic Scholar API (free key optional), CrossRef API (public), Papers With Code API (public), DBLP API (public)
- No authentication tokens for arXiv, CrossRef, Papers With Code, or DBLP
- Semantic Scholar API key is optional (passed via --ss-api-key or env var)
- Saves analysis results to `LITERATURE_MEMORY_DIR` (default: `~/Documents/AcademicTrends/`)
