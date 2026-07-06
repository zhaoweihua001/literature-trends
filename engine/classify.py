import re
from collections import defaultdict

# Keyword-to-category mapping (ordered by priority - first match wins)
CATEGORY_RULES = [
    ("foundation_model", [
        r"\bfoundation\s*model", r"\bCLIP\b", r"\bViLT\b", r"\bBLIP\b",
        r"\bpretrained\s*(language|vision)\s*model", r"\bvisual\s*language\s*model",
        r"\bVLM\b", r"\bmultimodal\s*foundation",
    ]),
    ("transformer_based", [
        r"\btransformer", r"\bViT\b", r"\bself.?attention\b", r"\battention\s*mechanism",
        r"\bswin\b", r"\bMaSTeR\b",
    ]),
    ("meta_learning", [
        r"\bmeta.?learn", r"\bMAML\b", r"\bmeta.?training", r"\blearn\s*to\s*learn",
        r"\bepisodic\b", r"\bmeta.?test", r"\binner.?loop\b", r"\bouter.?loop\b",
    ]),
    ("prompt_tuning", [
        r"\bprompt\b", r"\bprompt.?tun", r"\bprompt.?engineer", r"\bprefix.?tun",
        r"\bsoft\s*prompt", r"\bvisual\s*prompt", r"\bcontext\s*optim",
    ]),
    ("data_augmentation", [
        r"\bdata\s*augment", r"\bsynthetic\s*sample", r"\bimage\s*generat",
        r"\bGAN\b", r"\bdiffusion\s*based", r"\bstyle\s*transfer",
        r"\bdata\s*generat", r"\bself.?supervised\s*pretraining",
    ]),
    ("transfer_learning", [
        r"\bfine.?tun", r"\btransfer\s*learn", r"\bdomain\s*adapt",
        r"\bdomain\s*general", r"\bpre.?train.*fine.?tun",
        r"\bknowledge\s*distill",
    ]),
    ("generative", [
        r"\bgenerative\s*model", r"\bdiffusion\b", r"\bVAE\b",
        r"\bflow.?based", r"\bnormalizing\s*flow", r"\bautoregressive",
    ]),
    ("graph_neural_network", [
        r"\bgraph\s*neural", r"\bGNN\b", r"\bgraph\s*network",
        r"\bgraph\s*attention", r"\bGCN\b", r"\bgraph\s*convolution",
    ]),
    ("metric_learning", [
        r"\bmetric.?learn", r"\bsiamese\b", r"\bcontrastive\s*loss",
        r"\btriplet\s*loss", r"\bcosine\s*similarity", r"\bprototypical",
        r"\brelation.?net", r"\bmatching\s*network",
    ]),
    ("ensemble", [
        r"\bensemble", r"\bmulti.?view", r"\baggregat", r"\bcommittee",
        r"\bconsensus\b", r"\bboosting\b",
    ]),
]


def classify_paper(abstract: str, title: str) -> str:
    """Classify a paper into a method category based on title + abstract keywords.

    Returns category string. Falls back to "other" if no rules match.
    """
    text = f"{title} {abstract}".lower()

    for category, patterns in CATEGORY_RULES:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return category

    return "other"


def _determine_category_trend(yearly_counts: dict[int, int]) -> str:
    """Determine if a category is growing/stable/declining based on year-over-year changes."""
    if len(yearly_counts) < 2:
        return "unknown"

    sorted_years = sorted(yearly_counts.keys())
    recent_years = sorted_years[-3:] if len(sorted_years) >= 3 else sorted_years
    mid_point = len(recent_years) // 2

    first_half = sum(yearly_counts.get(recent_years[i], 0) for i in range(mid_point))
    second_half = sum(yearly_counts.get(recent_years[i], 0) for i in range(mid_point, len(recent_years)))

    if first_half == 0 and second_half > 0:
        return "fast_growing"
    if first_half == 0:
        return "unknown"

    ratio = second_half / first_half
    if ratio > 1.5:
        return "fast_growing"
    elif ratio > 1.1:
        return "growing"
    elif ratio < 0.5:
        return "declining"
    elif ratio < 0.9:
        return "slow_declining"
    else:
        return "stable"


def classify_all(papers: list[dict]) -> list[dict]:
    """Add method_category to each paper record."""
    for paper in papers:
        if "method_category" not in paper:
            paper["method_category"] = classify_paper(
                paper.get("abstract", ""),
                paper.get("title", "")
            )
    return papers


def build_category_stats(papers: list[dict]) -> dict:
    """Build method_categories summary dict from classified papers."""
    categories = defaultdict(lambda: {
        "count": 0,
        "citations": [],
        "years": defaultdict(int),
        "papers": []
    })

    for paper in papers:
        cat = paper.get("method_category", "other")
        categories[cat]["count"] += 1

        cit = paper.get("citation_count")
        if cit is not None:
            categories[cat]["citations"].append(cit)

        year = paper.get("year")
        if year:
            categories[cat]["years"][year] += 1

        categories[cat]["papers"].append({
            "arxiv_id": paper.get("arxiv_id"),
            "title": paper.get("title"),
            "year": paper.get("year"),
            "citation_count": paper.get("citation_count"),
        })

    result = {}
    for cat, data in categories.items():
        citations = data["citations"]
        avg_cit = sum(citations) / len(citations) if citations else 0
        trend = _determine_category_trend(data["years"])

        # Top papers by citation
        sorted_papers = sorted(data["papers"], key=lambda p: p.get("citation_count") or 0, reverse=True)

        result[cat] = {
            "count": data["count"],
            "avg_citation": round(avg_cit, 1),
            "trend": trend,
            "top_papers": sorted_papers[:5],
        }

    return result
