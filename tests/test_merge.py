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
    # Papers now need SS enrichment that includes CCF-A venue to pass filter
    arxiv_papers = [
        {"arxiv_id": "2303.12345", "title": "Paper A", "year": 2024},
        {"arxiv_id": "2304.67890", "title": "Paper B", "year": 2024},
    ]
    # SS enrichment must include venue_raw mapping to CCF-A for paper to survive filter
    enrichment = {
        "2303.12345": {
            "citation_count": 85,
            "s2_url": "...",
            "venue_raw": "CVPR",
            "publication_types": [],
        },
        "2304.67890": {
            "citation_count": 10,
            "s2_url": "...",
            "venue_raw": "ECCV",
            "publication_types": [],
        },
    }
    result, stats = merge_papers(arxiv_papers, enrichment, {}, {})
    assert len(result) == 2
    assert result[0].get("citation_count") == 85
    assert result[0].get("venue_abbr") == "CVPR"
    assert result[1].get("venue_abbr") == "ECCV"


def test_merge_filters_non_ccf_papers():
    """Papers without CCF-A/B venue should be filtered out."""
    arxiv_papers = [
        {"arxiv_id": "2303.12345", "title": "Good paper", "year": 2024},
        {"arxiv_id": "2304.67890", "title": "Non-CCF paper", "year": 2024},
    ]
    enrichment = {
        "2303.12345": {
            "citation_count": 50,
            "s2_url": "...",
            "venue_raw": "CVPR",
            "publication_types": [],
        },
        "2304.67890": {
            "citation_count": 1,
            "s2_url": "...",
            "venue_raw": "Some Obscure Workshop",
            "publication_types": [],
        },
    }
    result, stats = merge_papers(arxiv_papers, enrichment, {}, {})
    assert len(result) == 1
    assert result[0]["arxiv_id"] == "2303.12345"
    assert stats["no_venue_found"] == 1  # workshop doesn't resolve


def test_merge_filters_journal_preprint():
    """Journal papers without DOI/publication evidence should be filtered out."""
    arxiv_papers = [
        {"arxiv_id": "2303.12345", "title": "Published Journal", "year": 2024, "doi": "10.1234/valid"},
        {"arxiv_id": "2304.67890", "title": "Unpublished Preprint", "year": 2024},
    ]
    enrichment = {
        "2303.12345": {
            "citation_count": 50,
            "s2_url": "...",
            "venue_raw": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "publication_types": [],
        },
        "2304.67890": {
            "citation_count": 5,
            "s2_url": "...",
            "venue_raw": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
            "publication_types": [],
        },
    }
    crossref = {
        "10.1234/valid": {
            "published_date": "2024-06-01",
            "publisher": "IEEE",
        }
    }
    result, _ = merge_papers(arxiv_papers, enrichment, crossref, {})
    assert len(result) == 1
    assert result[0]["arxiv_id"] == "2303.12345"


def test_merge_papers_preserves_order():
    papers = [
        {"arxiv_id": "2303.00001", "year": 2024},
        {"arxiv_id": "2303.00002", "year": 2024},
    ]
    # Both need venue to survive filter
    enrichment = {
        "2303.00001": {"citation_count": 1, "s2_url": "", "venue_raw": "CVPR", "publication_types": []},
        "2303.00002": {"citation_count": 1, "s2_url": "", "venue_raw": "ECCV", "publication_types": []},
    }
    result, _ = merge_papers(papers, enrichment, {}, {})
    assert result[0]["arxiv_id"] == "2303.00001"
    assert result[1]["arxiv_id"] == "2303.00002"
