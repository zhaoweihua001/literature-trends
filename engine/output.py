import json
from collections import Counter


def build_category_trends(categories: dict) -> dict:
    """Add trend direction text to each method category."""
    result = {}
    for cat, data in categories.items():
        result[cat] = {
            "count": data["count"],
            "avg_citation": data["avg_citation"],
            "trend": data["trend"],
            "top_papers": data["top_papers"],
        }
    return result


def build_keyword_trends(papers: list[dict]) -> dict:
    """Extract keyword trends from papers."""
    # Focus keywords to track
    tracked_keywords = [
        "transformer", "meta-learning", "foundation model", "prompt",
        "domain adaptation", "generative", "diffusion", "contrastive",
        "self-supervised", "knowledge distillation", "attention"
    ]

    # Count occurrences per year
    yearly = {}
    for paper in papers:
        year = paper.get("year")
        if not year:
            continue
        if year not in yearly:
            yearly[year] = Counter()
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

        for keyword in tracked_keywords:
            if keyword.lower() in text:
                yearly[year][keyword] += 1

    # Build result
    result = {}
    for keyword in tracked_keywords:
        counts = {}
        for year in sorted(yearly.keys()):
            counts[str(year)] = yearly[year].get(keyword, 0)

        # Determine trend
        sorted_years = sorted(yearly.keys())
        if len(sorted_years) >= 2:
            first = sum(yearly[y].get(keyword, 0) for y in sorted_years[:len(sorted_years)//2])
            second = sum(yearly[y].get(keyword, 0) for y in sorted_years[len(sorted_years)//2:])
            if first == 0 and second > 0:
                trend = "fast_growing"
            elif first == 0:
                trend = "none"
            else:
                ratio = second / first
                trend = "fast_growing" if ratio > 1.5 else "growing" if ratio > 1.1 else "declining" if ratio < 0.7 else "stable"
        else:
            trend = "unknown"

        result[keyword] = dict(counts)
        result[keyword]["trend"] = trend

    return result


def build_benchmark_trends(benchmarks: list[dict]) -> dict:
    """Convert Papers With Code benchmark data into per-dataset trend dict."""
    result = {}
    for bench in benchmarks:
        dataset = bench.get("dataset_slug", "unknown")
        yearly = {}
        for metric in bench.get("metrics", []):
            year = metric.get("year")
            if year:
                yearly[str(year)] = {
                    "best": metric.get("best"),
                    "method": metric.get("method", ""),
                }
        result[dataset] = yearly
        result[dataset]["saturation"] = bench.get("saturation", "unknown")
    return result


def build_venue_distribution(venues: dict) -> dict:
    """Convert venue stats to output format."""
    return venues


def build_yearly_stats(papers: list[dict]) -> list[dict]:
    """Build yearly statistics from papers."""
    by_year = {}
    for paper in papers:
        year = paper.get("year")
        if not year:
            continue
        if year not in by_year:
            by_year[year] = {"paper_count": 0, "citations": [], "venues": Counter()}

        by_year[year]["paper_count"] += 1
        cit = paper.get("citation_count")
        if cit is not None:
            by_year[year]["citations"].append(cit)
        venue = paper.get("venue", "")
        if venue:
            by_year[year]["venues"][venue] += 1

    stats = []
    for year in sorted(by_year.keys()):
        data = by_year[year]
        avg_cit = sum(data["citations"]) / len(data["citations"]) if data["citations"] else 0
        top_venues = [v for v, _ in data["venues"].most_common(5)]
        stats.append({
            "year": year,
            "paper_count": data["paper_count"],
            "avg_citation": round(avg_cit, 1),
            "top_venues": top_venues,
        })
    return stats


def build_high_impact_papers(papers: list[dict], top_n: int = 10) -> list[dict]:
    """Return top N papers by citation count."""
    with_citations = [p for p in papers if p.get("citation_count") is not None]
    sorted_papers = sorted(with_citations, key=lambda p: p["citation_count"], reverse=True)
    return [
        {
            "title": p["title"],
            "citations": p["citation_count"],
            "year": p.get("year"),
            "venue": p.get("venue", ""),
            "method_category": p.get("method_category", "other"),
            "arxiv_id": p.get("arxiv_id", ""),
        }
        for p in sorted_papers[:top_n]
    ]


def build_output(
    papers: list[dict],
    meta: dict,
    method_categories: dict,
    keyword_trends: dict,
    benchmark_trends: dict,
    venue_distribution: dict,
) -> dict:
    """Assemble the final output JSON structure."""
    yearly_stats = build_yearly_stats(papers)
    high_impact = build_high_impact_papers(papers)

    return {
        "meta": meta,
        "papers": papers,
        "method_categories": method_categories,
        "yearly_stats": yearly_stats,
        "keyword_trends": keyword_trends,
        "benchmark_trends": benchmark_trends,
        "high_impact_papers": high_impact,
        "venue_distribution": venue_distribution,
    }
