def dedup_by_id(papers: list[dict]) -> list[dict]:
    """Remove duplicate papers by arxiv_id. Keeps first occurrence."""
    seen = set()
    result = []
    for paper in papers:
        pid = paper.get("arxiv_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            result.append(paper)
        elif not pid:
            result.append(paper)
    return result


def merge_papers(
    arxiv_papers: list[dict],
    ss_enrichment: dict[str, dict],
    crossref_data: dict[str, dict],
    pwc_map: dict[str, list],
    paper_venues: dict[str, str] = None
) -> list[dict]:
    """Merge enrichment data from all sources into arxiv_papers.

    Args:
        arxiv_papers: list of paper dicts from ArxivFetcher
        ss_enrichment: dict keyed by arxiv_id from Semantic Scholar
        crossref_data: dict keyed by DOI from CrossRef
        pwc_map: dict keyed by arxiv_id -> list[str] (benchmark names)
        paper_venues: dict keyed by arxiv_id -> venue string from DBLP

    Returns:
        Enriched paper list
    """
    if paper_venues is None:
        paper_venues = {}

    merged = []
    for paper in arxiv_papers:
        enriched = dict(paper)  # copy
        arxiv_id = paper.get("arxiv_id", "")
        doi = paper.get("doi", "")

        # Enrich from Semantic Scholar
        if arxiv_id in ss_enrichment:
            ss = ss_enrichment[arxiv_id]
            enriched["citation_count"] = ss.get("citation_count")
            enriched["s2_url"] = ss.get("s2_url")

        # Enrich from CrossRef (by DOI)
        if doi and doi in crossref_data:
            cr = crossref_data[doi]
            enriched["journal"] = cr.get("journal", "")
            enriched["publisher"] = cr.get("publisher", "")
            enriched["published_date"] = cr.get("published_date", "")

        # Enrich with benchmark info
        if arxiv_id in pwc_map:
            enriched["benchmark_results"] = pwc_map[arxiv_id]

        # Enrich with DBLP venue
        if arxiv_id in paper_venues:
            enriched["venue"] = paper_venues[arxiv_id]

        merged.append(enriched)

    return merged
