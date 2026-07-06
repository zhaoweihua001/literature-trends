import requests
import time
from typing import Optional


class SemanticScholarFetcher:
    """Fetch citation data from Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AcademicTrendsSkill/1.0"})
        if api_key:
            self.session.headers.update({"x-api-key": api_key})
        self._last_request_time = 0

    def fetch_batch(self, arxiv_ids: list[str], batch_size: int = 10) -> dict[str, dict]:
        """Look up citation data for papers by arXiv ID.

        Returns dict keyed by arxiv_id with citation data.
        Uses small batches with retry to avoid 429 rate limiting.
        """
        if not arxiv_ids:
            return {}

        results = {}
        for i in range(0, len(arxiv_ids), batch_size):
            batch = arxiv_ids[i:i + batch_size]
            batch_results = self._fetch_with_retry(batch)
            results.update(batch_results)
            # Extra delay between batches to avoid cumulative rate limiting
            time.sleep(1.0)

        return results

    def _fetch_with_retry(self, arxiv_ids: list[str], max_retries: int = 3) -> dict[str, dict]:
        """Fetch a batch with retry and exponential backoff on 429."""
        for attempt in range(max_retries):
            self._rate_limit()
            url = "https://api.semanticscholar.org/graph/v1/paper/batch"
            params = {
                "fields": "citationCount,citations.title,citations.isInfluential,title,year,externalIds,venue,publicationTypes"
            }
            payload = {"ids": [f"ArXiv:{a}" for a in arxiv_ids]}
            try:
                resp = self.session.post(url, params=params, json=payload, timeout=30)
                if resp.status_code == 429:
                    wait = (attempt + 1) * 5  # 5s, 10s, 15s
                    print(f"  SS rate limited, waiting {wait}s...", file=__import__('sys').stderr)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                results = resp.json()
                output = {}
                for item in results:
                    if item is None:
                        continue
                    ext_ids = item.get("externalIds") or {}
                    arxiv_id = ext_ids.get("ArXiv", "")
                    if not arxiv_id:
                        continue
                    citation_count = item.get("citationCount", 0) or 0
                    citations_list = item.get("citations") or []
                    influential_count = sum(
                        1 for c in citations_list if c.get("isInfluential")
                    )
                    venue_raw = item.get("venue", "") or ""
                    pub_types = item.get("publicationTypes") or []
                    output[arxiv_id] = {
                        "citation_count": citation_count,
                        "influential_citations": influential_count,
                        "citation_growth": None,
                        "s2_url": f"https://www.semanticscholar.org/paper/ArXiv:{arxiv_id}",
                        "title": item.get("title", ""),
                        "year": item.get("year"),
                        "external_ids": ext_ids,
                        "venue_raw": venue_raw,
                        "publication_types": pub_types,
                    }
                return output
            except (requests.RequestException, ValueError):
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
                return {}

        return {}

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 0.6:
            time.sleep(0.6 - elapsed)
        self._last_request_time = time.time()
