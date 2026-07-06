import pytest
from engine.fetchers.arxiv import ArxivFetcher


def test_arxiv_search_returns_papers():
    """Verify ArxivFetcher returns paper records for a valid topic."""
    fetcher = ArxivFetcher(cache_dir=None)
    results = fetcher.fetch(
        topic="few-shot image classification",
        categories=["cs.CV"],
        max_results=10,
        start_year=2024,
        end_year=2026
    )
    assert len(results) > 0
    for paper in results:
        assert "arxiv_id" in paper
        assert "title" in paper
        assert "abstract" in paper
        assert "year" in paper
        assert "month" in paper
        assert "categories" in paper


def test_arxiv_search_with_categories_filters_correctly():
    """Verify only papers in requested categories are returned."""
    fetcher = ArxivFetcher(cache_dir=None)
    results = fetcher.fetch(
        topic="transformer",
        categories=["cs.CV"],
        max_results=5,
        start_year=2025,
        end_year=2026
    )
    for paper in results:
        categories = paper.get("categories", [])
        assert any(c.startswith("cs.CV") for c in categories), \
            f"Paper {paper['arxiv_id']} has no cs.CV category"


def test_arxiv_search_returns_empty_for_gibberish():
    """Verify nonsense query returns empty list, not crash."""
    fetcher = ArxivFetcher(cache_dir=None)
    results = fetcher.fetch(
        topic="zxzxjqkwkqlmcnv",
        categories=["cs.CV"],
        max_results=10,
        start_year=2024,
        end_year=2026
    )
    assert results == []
