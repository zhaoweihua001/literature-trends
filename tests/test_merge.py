import pytest
from engine.merge import merge_papers, dedup_by_id

def test_dedup_by_id_removes_duplicates():
    papers = [
        {"arxiv_id": "2303.12345", "title": "Paper A"},
        {"arxiv_id": "2303.12345", "title": "Paper A"},  # dup
        {"arxiv_id": "2304.67890", "title": "Paper B"},
    ]
    result = dedup_by_id(papers)
    assert len(result) == 2

def test_merge_papers_enriches_with_citation():
    arxiv_papers = [
        {"arxiv_id": "2303.12345", "title": "Paper A", "year": 2024},
        {"arxiv_id": "2304.67890", "title": "Paper B", "year": 2024},
    ]
    enrichment = {
        "2303.12345": {"citation_count": 85, "s2_url": "..."},
    }
    result = merge_papers(arxiv_papers, enrichment, {}, {})
    assert result[0].get("citation_count") == 85
    assert result[1].get("citation_count") is None  # no enrichment

def test_merge_papers_preserves_order():
    papers = [
        {"arxiv_id": "2303.00001", "year": 2024},
        {"arxiv_id": "2303.00002", "year": 2024},
    ]
    result = merge_papers(papers, {}, {}, {})
    assert result[0]["arxiv_id"] == "2303.00001"
    assert result[1]["arxiv_id"] == "2303.00002"
