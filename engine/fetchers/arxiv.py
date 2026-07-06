import requests
import xml.etree.ElementTree as ET
import time
import re
from typing import Optional

ARXIV_API_URL = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
RETRY_DELAY = 2


class ArxivFetcher:
    """Fetch papers from arXiv API by topic search + category filter."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AcademicTrendsSkill/1.0 (mailto:user@example.com)"
        })

    def fetch(
        self,
        topic: str,
        categories: Optional[list[str]] = None,
        max_results: int = 200,
        start_year: int = 2023,
        end_year: int = 2026
    ) -> list[dict]:
        """Search arXiv API, return paper records evenly distributed across years.

        Splits queries by year so that results span the full date range instead of
        arXiv's default descending-date sort which returns mostly the most recent year.
        """
        years_range = list(range(end_year, start_year - 1, -1))
        per_year = max(1, max_results // len(years_range))
        all_papers = []

        for year in years_range:
            year_papers = self._fetch_single_year(topic, categories, year, per_year)
            all_papers.extend(year_papers)

        # Fill any remaining capacity from the most recent year
        if len(all_papers) < max_results:
            extra = self._fetch_single_year(
                topic, categories, end_year,
                max_results - len(all_papers), offset=per_year
            )
            all_papers.extend(extra)

        return all_papers[:max_results]

    def _build_query(self, topic: str, categories: Optional[list[str]]) -> str:
        """Build arXiv search query from topic and categories."""
        query_parts = [f"all:{topic}"]
        if categories:
            cat_query = " OR ".join(f"cat:{c}" for c in categories)
            query_parts.append(f"({cat_query})")
        return " AND ".join(query_parts)

    def _fetch_single_year(
        self, topic: str, categories: Optional[list[str]],
        year: int, count: int, offset: int = 0
    ) -> list[dict]:
        """Fetch papers from a single year using arXiv date-range query."""
        query = self._build_query(topic, categories)
        date_from = f"{year}0101000000"
        date_to = f"{year}1231235959"
        date_query = f"({query}) AND submittedDate:[{date_from} TO {date_to}]"

        papers = []
        while len(papers) < count:
            params = {
                "search_query": date_query,
                "start": offset + len(papers),
                "max_results": min(100, count - len(papers)),
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            response = self._fetch_with_retry(ARXIV_API_URL, params=params)
            if response is None:
                break

            batch = self._parse_response(response.text)
            if not batch:
                break

            batch = [p for p in batch if p["year"] == year]
            papers.extend(batch)
            time.sleep(3)

        return papers[:count]

    def _fetch_with_retry(self, url: str, params: dict, max_retries: int = MAX_RETRIES):
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response
            except (requests.RequestException, ConnectionError) as e:
                if attempt < max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                    continue
                return None
        return None

    def _parse_response(self, xml_text: str) -> list[dict]:
        """Parse arXiv Atom XML response into paper dicts."""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }
        root = ET.fromstring(xml_text)
        papers = []

        for entry in root.findall("atom:entry", ns):
            try:
                arxiv_id = self._extract_id(entry)
                title_elem = entry.find("atom:title", ns)
                title = self._clean_html(title_elem.text.strip()) if title_elem is not None else ""
                abstract_elem = entry.find("atom:summary", ns)
                abstract = self._clean_html(abstract_elem.text.strip()) if abstract_elem is not None else ""
                published = entry.find("atom:published", ns)
                year = int(published.text[:4]) if published is not None else 0
                month = int(published.text[5:7]) if published is not None else 0

                # Authors
                authors = []
                for author_elem in entry.findall("atom:author", ns):
                    name_elem = author_elem.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append(name_elem.text.strip())

                # Categories
                categories = []
                for cat_elem in entry.findall("atom:category", ns):
                    term = cat_elem.get("term", "")
                    categories.append(term)

                # DOI from arXiv comment
                doi = None
                comment_text = ""
                comment = entry.find("arxiv:comment", ns)
                if comment is not None and comment.text:
                    comment_text = comment.text.strip()
                    doi_match = re.search(r"doi:(\S+)", comment_text)
                    if doi_match:
                        doi = doi_match.group(1)

                papers.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "month": month,
                    "abstract": abstract,
                    "categories": categories,
                    "primary_category": categories[0] if categories else "",
                    "doi": doi,
                    "comment": comment_text,
                    "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}"
                })
            except (AttributeError, ValueError, TypeError) as e:
                continue  # skip malformed entries

        return papers

    def _extract_id(self, entry) -> str:
        """Extract arXiv ID from the entry's id URL like http://arxiv.org/abs/2303.12345v1"""
        id_elem = entry.find("atom:id", {
            "atom": "http://www.w3.org/2005/Atom"
        })
        url = id_elem.text.strip() if id_elem is not None else ""
        # Extract ID like 2303.12345 from URL
        match = re.search(r"abs/(\d+\.\d+)", url)
        return match.group(1) if match else url

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
