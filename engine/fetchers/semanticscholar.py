import requests
import time
from typing import Optional


class SemanticScholarFetcher:
    """Fetch citation data from Semantic Scholar API.

    Uses individual paper lookups (not batch API) which works better without
    an API key at ~100 requests per minute.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AcademicTrendsSkill/1.0"})
        if api_key:
            self.session.headers.update({"x-api-key": api_key})
        self._last_request_time = 0

    def fetch_batch(self, arxiv_ids: list[str], batch_size: int = 50) -> dict[str, dict]:
        """Look up citation data for papers by arXiv ID.

        Uses individual lookups (100 req/min free) instead of batch API
        (which is heavily rate-limited without a key).
        Only queries the first batch_size papers to stay within time budget.
        """
        if not arxiv_ids:
            return {}

        actual_batch = arxiv_ids[:batch_size]
        results = {}
        for arxiv_id in actual_batch:
            result = self._fetch_paper_by_id(arxiv_id)
            if result:
                results[arxiv_id] = result
            time.sleep(0.6)  # ~100 req/min rate limit

        return results

    def _fetch_paper_by_id(self, arxiv_id: str) -> Optional[dict]:
        """Look up a single paper by arXiv ID."""
        self._rate_limit()
        url = f"{self.BASE_URL}/paper/ArXiv:{arxiv_id}"
        params = {
            "fields": "citationCount,citations.title,citations.isInfluential,title,year,externalIds,venue,publicationTypes"
        }
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 429:
                print(f"  SS rate limited, waiting 5s...", file=__import__('sys').stderr)
                time.sleep(5)
                return None
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()

            citation_count = data.get("citationCount", 0) or 0
            citations_list = data.get("citations") or []
            influential_count = sum(
                1 for c in citations_list if c.get("isInfluential")
            )
            venue_raw = data.get("venue", "") or ""
            pub_types = data.get("publicationTypes") or []
            ext_ids = data.get("externalIds") or {}

            return {
                "citation_count": citation_count,
                "influential_citations": influential_count,
                "citation_growth": None,
                "s2_url": f"https://www.semanticscholar.org/paper/ArXiv:{arxiv_id}",
                "title": data.get("title", ""),
                "year": data.get("year"),
                "external_ids": ext_ids,
                "venue_raw": venue_raw,
                "publication_types": pub_types,
            }
        except (requests.RequestException, ValueError):
            return None

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 0.6:
            time.sleep(0.6 - elapsed)
        self._last_request_time = time.time()
