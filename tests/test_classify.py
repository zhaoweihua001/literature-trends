import pytest
from engine.classify import classify_paper, classify_all, build_category_stats

def test_classify_paper_meta_learning():
    result = classify_paper(
        "We propose a meta-learning approach for few-shot classification using MAML",
        "Meta-Learning for Few-Shot Classification"
    )
    assert result == "meta_learning"

def test_classify_paper_transformer():
    result = classify_paper(
        "We use Vision Transformers to improve few-shot image recognition",
        "ViT for Few-Shot Learning"
    )
    assert result == "transformer_based"

def test_classify_all_adds_categories():
    papers = [
        {"title": "MAML++", "abstract": "meta-learning approach for few-shot", "arxiv_id": "1"},
        {"title": "ViT for Few-Shot", "abstract": "transformer-based method", "arxiv_id": "2"},
    ]
    result = classify_all(papers)
    assert result[0].get("method_category") == "meta_learning"
    assert result[1].get("method_category") == "transformer_based"

def test_build_category_stats():
    papers = [
        {"method_category": "meta_learning", "citation_count": 50, "year": 2024},
        {"method_category": "meta_learning", "citation_count": 30, "year": 2024},
        {"method_category": "transformer_based", "citation_count": 80, "year": 2024},
    ]
    stats = build_category_stats(papers)
    assert stats["meta_learning"]["count"] == 2
    assert stats["meta_learning"]["avg_citation"] == 40
    assert stats["transformer_based"]["count"] == 1
