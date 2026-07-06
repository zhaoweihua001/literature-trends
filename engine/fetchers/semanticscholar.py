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

    def fetch_batch(self, arxiv_ids: list[str], batch_size: int = 50) -> dict[str, dict]:
        """Look up citation data for papers by arXiv ID.

        Returns dict keyed by arxiv_id with citation data.
        Batches requests to stay within rate limits.
        """
        if not arxiv_ids:
            return {}

        results = {}
        for i in range(0, len(arxiv_ids), batch_size):
            batch = arxiv_ids[i:i + batch_size]
            batch_results = self._fetch_batch_internal(batch)
            results.update(batch_results)

        return results

    def _fetch_batch_internal(self, arxiv_ids: list[str]) -> dict[str, dict]:
        """Look up multiple papers via the Semantic Scholar batch API.

        POST up to 50 ArXiv IDs to the /paper/batch endpoint.
        Returns dict keyed by arxiv_id with citation data.
        """
        if not arxiv_ids:
            return {}
        self._rate_limit()
        url = "https://api.semanticscholar.org/graph/v1/paper/batch"
        params = {
            "fields": "citationCount,citations.title,citations.isInfluential,title,year,externalIds"
        }
        payload = {"ids": [f"ArXiv:{a}" for a in arxiv_ids]}
        try:
            resp = self.session.post(url, params=params, json=payload, timeout=30)
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
                output[arxiv_id] = {
                    "citation_count": citation_count,
                    "influential_citations": influential_count,
                    "citation_growth": None,
                    "s2_url": f"https://www.semanticscholar.org/paper/ArXiv:{arxiv_id}",
                    "title": item.get("title", ""),
                    "year": item.get("year"),
                    "external_ids": ext_ids,
                }
            return output
        except (requests.RequestException, ValueError):
            return {}

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 0.6:
            time.sleep(0.6 - elapsed)
        self._last_request_time = time.time()
