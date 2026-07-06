import pytest
from engine.fetchers.crossref import CrossRefFetcher


def test_fetch_by_dois_returns_results():
    fetcher = CrossRefFetcher()
    dois = ["10.1109/CVPR.2024.12345"]
    results = fetcher.fetch_by_dois(dois)
    assert isinstance(results, dict)


def test_fetch_by_dois_empty_input():
    fetcher = CrossRefFetcher()
    results = fetcher.fetch_by_dois([])
    assert results == {}


def test_fetch_by_dois_invalid_doi():
    fetcher = CrossRefFetcher()
    results = fetcher.fetch_by_dois(["10.9999/invalid-doi-12345"])
    assert isinstance(results, dict)
