import requests
import time
import re
from typing import Optional


class DBLPFetcher:
    """Fetch venue/publication info from DBLP API."""

    BASE_URL = "https://dblp.org/search/publ/api"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AcademicTrendsSkill/1.0"})
        self._last_request_time = 0

    def fetch_venue_stats(self, papers: list[dict]) -> dict:
        """For each paper, try to find its DBLP entry to extract venue."""
        if not papers:
            return {"venue_distribution": {}, "paper_venues": {}}

        venue_counts = {}
        paper_venues = {}

        # Sample: query DBLP for each paper's publication venue
        for paper in papers[:50]:  # limit to 50 to avoid aggressive rate limiting
            self._rate_limit()
            venue = self._search_paper_venue(paper)
            if venue:
                paper_venues[paper["arxiv_id"]] = venue
                venue_counts[venue] = venue_counts.get(venue, 0) + 1

        # Estimate venue distribution by matching venue names in abstracts
        venue_keywords = {
            "CVPR": r"\bCVPR\b",
            "ICCV": r"\bICCV\b",
            "ECCV": r"\bECCV\b",
            "NeurIPS": r"\bNeurIPS\b|NIPS",
            "ICLR": r"\bICLR\b",
            "AAAI": r"\bAAAI\b",
            "ICML": r"\bICML\b",
            "IEEE TPAMI": r"IEEE.*TPAMI|IEEE.*Pattern.*Analysis",
            "IJCV": r"\bIJCV\b",
            "IEEE TIP": r"IEEE.*Image\s*Process",
        }

        for paper in papers:
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
            for venue, pattern in venue_keywords.items():
                if re.search(pattern, text, re.IGNORECASE):
                    venue_counts[venue] = venue_counts.get(venue, 0) + 1
                    break

        # Sort venues by count
        sorted_venues = dict(sorted(venue_counts.items(), key=lambda x: -x[1]))

        return {
            "venue_distribution": sorted_venues,
            "paper_venues": paper_venues
        }

    def _search_paper_venue(self, paper: dict) -> Optional[str]:
        """Search DBLP for a paper's venue."""
        try:
            title = paper.get("title", "")
            params = {
                "q": title[:100],
                "format": "json",
                "hits": 3
            }
            resp = self.session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            hits = (data.get("result", {})
                    .get("hits", {})
                    .get("hit", []))
            for hit in hits:
                info = hit.get("info", {})
                venue = info.get("venue", "")
                if venue:
                    return venue
        except (requests.RequestException, ValueError, KeyError, AttributeError):
            pass
        return None

    def _rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self._last_request_time = time.time()
