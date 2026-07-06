import pytest
from engine.fetchers.paperswithcode import PapersWithCodeFetcher


def test_fetch_returns_benchmark():
    fetcher = PapersWithCodeFetcher()
    results = fetcher.fetch("few-shot image classification")
    assert "benchmarks" in results
    assert "paper_to_benchmark" in results


def test_fetch_gibberish_returns_empty():
    fetcher = PapersWithCodeFetcher()
    results = fetcher.fetch("zxzxjqkwkqlmcnv")
    assert results == {"benchmarks": [], "paper_to_benchmark": {}}
