"""Merge enrichment data and filter papers by CCF venue ranking.

Rules:
- CCF-A/B conference papers: always included
- CCF-A/B journal papers: included only if published (has DOI/crossref data)
- Non CCF-A/B: excluded
- arXiv-only with no venue: excluded
- Output papers are labelled with venue abbreviation (no CCF grade shown)
"""

from engine.ccf_rankings import normalize_venue, is_ccf_a_b, JOURNAL_VENUES


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


def _resolve_venue_from_ss(ss_data: dict) -> str | None:
    """Try to extract a CCF-recognizable venue abbreviation from Semantic Scholar data."""
    raw = ss_data.get("venue_raw", "")
    if raw:
        abbr = normalize_venue(raw)
        if abbr:
            return abbr
    return None


def _resolve_venue_from_dblp(paper_venues: dict, arxiv_id: str) -> str | None:
    """Try to extract venue from DBLP data."""
    raw = paper_venues.get(arxiv_id, "")
    if raw:
        abbr = normalize_venue(raw)
        if abbr:
            return abbr
    return None


def _is_journal_published(paper: dict, crossref_data: dict) -> bool:
    """Check if a journal paper has been formally published (not just a preprint).

    A journal paper is "published" if:
    - It has a DOI that resolved in CrossRef, OR
    - CrossRef returned a published_date, OR
    - Semantic Scholar's publication_types includes "JournalArticle"
    """
    doi = paper.get("doi", "")
    if doi and doi in crossref_data:
        cr = crossref_data[doi]
        if cr.get("published_date") or cr.get("publisher"):
            return True

    # Check SS publication types
    ss = paper.get("_ss_enrichment", {})
    pub_types = ss.get("publication_types", [])
    if "JournalArticle" in pub_types:
        return True

    # No DOI = preprint, not published
    return False


def merge_papers(
    arxiv_papers: list[dict],
    ss_enrichment: dict[str, dict],
    crossref_data: dict[str, dict],
    pwc_map: dict[str, list],
    paper_venues: dict[str, str] = None
) -> list[dict]:
    """Merge enrichment from all sources, resolve venue, filter by CCF.

    Returns enriched & filtered paper list. Adds 'venue_abbr' field.
    Also returns statistics on what was filtered out.
    """
    if paper_venues is None:
        paper_venues = {}

    stats = {
        "total_raw": len(arxiv_papers),
        "no_venue_found": 0,
        "not_ccf_a_b": 0,
        "journal_preprint": 0,
        "ccf_a_conference": 0,
        "ccf_b_conference": 0,
        "ccf_a_journal": 0,
        "ccf_b_journal": 0,
    }

    merged = []
    for paper in arxiv_papers:
        enriched = dict(paper)
        arxiv_id = paper.get("arxiv_id", "")
        doi = paper.get("doi", "")

        # Store SS enrichment for later checks (not included in output)
        if arxiv_id in ss_enrichment:
            ss = ss_enrichment[arxiv_id]
            enriched["_ss_enrichment"] = ss
            enriched["citation_count"] = ss.get("citation_count")
            enriched["s2_url"] = ss.get("s2_url")

        # Enrich from CrossRef
        if doi and doi in crossref_data:
            cr = crossref_data[doi]
            enriched["journal"] = cr.get("journal", "")
            enriched["publisher"] = cr.get("publisher", "")
            enriched["published_date"] = cr.get("published_date", "")

        # Enrich with benchmark info
        if arxiv_id in pwc_map:
            enriched["benchmark_results"] = pwc_map[arxiv_id]

        # === Venue Resolution ===
        venue_abbr = None

        # Try Semantic Scholar first
        if arxiv_id in ss_enrichment:
            venue_abbr = _resolve_venue_from_ss(ss_enrichment[arxiv_id])

        # Fall back to DBLP
        if not venue_abbr:
            venue_abbr = _resolve_venue_from_dblp(paper_venues, arxiv_id)

        # Also check if arXiv comment contains acceptance info
        if not venue_abbr:
            comment = paper.get("comment", "") or ""
            for known_venue in ["CVPR", "ICCV", "ECCV", "NeurIPS", "ICML",
                                "AAAI", "IJCAI", "ICLR", "ACM MM"]:
                if known_venue.lower() in comment.lower():
                    venue_abbr = known_venue
                    break

        if not venue_abbr:
            # No venue found at all — exclude
            stats["no_venue_found"] += 1
            continue

        # Check CCF rank
        if not is_ccf_a_b(venue_abbr):
            stats["not_ccf_a_b"] += 1
            continue

        # For journal venues, require evidence of publication
        if venue_abbr in JOURNAL_VENUES:
            if not _is_journal_published(enriched, crossref_data):
                stats["journal_preprint"] += 1
                continue
            if venue_abbr in {"IEEE TPAMI", "IJCV", "IEEE TIP"}:
                stats["ccf_a_journal"] += 1
            else:
                stats["ccf_b_journal"] += 1
        else:
            # Conference venue
            if venue_abbr in {"CVPR", "ICCV", "NeurIPS", "ICML", "AAAI", "IJCAI", "ACM MM"}:
                stats["ccf_a_conference"] += 1
            else:
                stats["ccf_b_conference"] += 1

        # Set final venue abbreviation (no CCF grade shown)
        enriched["venue_abbr"] = venue_abbr
        enriched["venue"] = venue_abbr

        # Remove internal enrichment data from output
        enriched.pop("_ss_enrichment", None)

        merged.append(enriched)

    return merged, stats
