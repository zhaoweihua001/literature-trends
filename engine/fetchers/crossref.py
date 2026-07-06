import requests
import time
from typing import Optional


class CrossRefFetcher:
    """Fetch journal/DOI metadata from CrossRef API."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: str = "user@example.com"):
        self.mailto = mailto
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"AcademicTrendsSkill/1.0 (mailto:{mailto})"})
        self._last_request_time = 0

    def fetch_by_dois(self, dois: list[str]) -> dict[str, dict]:
        """Look up journal/DOI info for a list of DOIs.

        Returns dict keyed by DOI.
        """
        if not dois:
            return {}

        results = {}
        for doi in dois:
            self._rate_limit()
            data = self._fetch_single(doi)
            if data:
                results[doi] = data
        return results

    def _fetch_single(self, doi: str) -> Optional[dict]:
        """Fetch metadata for a single DOI."""
        url = f"{self.BASE_URL}/{doi}"
        try:
            resp = self.session.get(url, params={"mailto": self.mailto}, timeout=15)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json().get("message", {})

            return {
                "doi": doi,
                "publisher": data.get("publisher", ""),
                "journal": self._get_journal(data),
                "published_date": self._get_published_date(data),
                "title": (data.get("title") or [""])[0],
                "type": data.get("type", ""),
                "issn": (data.get("ISSN") or [""])[0] if data.get("ISSN") else "",
            }
        except (requests.RequestException, ValueError, KeyError):
            return None

    def _get_journal(self, data: dict) -> str:
        """Extract journal/proceedings name from message."""
        container = data.get("container-title") or []
        if container:
            return container[0]
        return data.get("short-container-title", [""])[0] if data.get("short-container-title") else ""

    def _get_published_date(self, data: dict) -> Optional[str]:
        """Extract published date from message."""
        dates = ["published-print", "published-online", "issued", "created"]
        for key in dates:
            date_info = data.get(key, {})
            parts = date_info.get("date-parts", [[]])[0]
            if parts:
                if len(parts) >= 3:
                    return f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
                elif len(parts) >= 2:
                    return f"{parts[0]}-{parts[1]:02d}"
                return str(parts[0])
        return ""

    def fetch_by_title(self, title: str) -> Optional[dict]:
        """Search CrossRef by title to find DOI."""
        self._rate_limit()
        try:
            params = {"query.title": title, "rows": 1}
            resp = self.session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("message", {}).get("items", [])
            if items:
                self._rate_limit()
                return self._fetch_single(items[0].get("DOI"))
        except (requests.RequestException, ValueError, KeyError):
            pass
        return None

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 0.05:
            time.sleep(0.05 - elapsed)
        self._last_request_time = time.time()
