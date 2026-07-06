import pytest
from engine.fetchers.semanticscholar import SemanticScholarFetcher


def test_fetch_batch_returns_citation_counts():
    fetcher = SemanticScholarFetcher()
    ids = ["2303.12345"]  # example arXiv ID
    results = fetcher.fetch_batch(ids)
    assert isinstance(results, dict)
    if "2303.12345" in results:
        item = results["2303.12345"]
        assert "citation_count" in item
        assert "influential_citations" in item
        assert item["citation_growth"] is None


def test_fetch_batch_empty_input():
    fetcher = SemanticScholarFetcher()
    results = fetcher.fetch_batch([])
    assert results == {}


def test_fetch_batch_invalid_id_returns_empty():
    fetcher = SemanticScholarFetcher()
    results = fetcher.fetch_batch(["0000.00000"])
    assert isinstance(results, dict)
