import pytest
from engine.output import build_output


def test_build_output_has_all_sections():
    papers = [
        {"arxiv_id": "1", "title": "A", "year": 2024, "method_category": "meta_learning", "citation_count": 50},
    ]
    meta = {"topic": "test", "years": "2024-2026"}
    categories = {"meta_learning": {"count": 1, "avg_citation": 50, "trend": "stable", "top_papers": []}}
    keywords = {"meta": {"2024": 1, "trend": "stable"}}
    benchmarks = {"bench1": {"saturation": "active", "2024": {"best": 90.0}}}
    venues = {"CVPR": {"count": 1, "trend": "stable"}}

    output = build_output(papers, meta, categories, keywords, benchmarks, venues)
    assert "meta" in output
    assert "papers" in output
    assert "method_categories" in output
    assert "keyword_trends" in output
    assert "benchmark_trends" in output
    assert "venue_distribution" in output
