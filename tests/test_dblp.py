import pytest
from engine.fetchers.dblp import DBLPFetcher


def test_fetch_venue_stats_returns_distribution():
    fetcher = DBLPFetcher()
    papers = [{"arxiv_id": "2303.12345", "title": "Test Paper", "authors": ["Zhang S"]}]
    results = fetcher.fetch_venue_stats(papers)
    assert "venue_distribution" in results
    assert "paper_venues" in results


def test_fetch_venue_stats_empty():
    fetcher = DBLPFetcher()
    results = fetcher.fetch_venue_stats([])
    assert results == {"venue_distribution": {}, "paper_venues": {}}
