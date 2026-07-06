import requests
from typing import Optional


class PapersWithCodeFetcher:
    """Fetch benchmark data from Papers With Code API."""

    BASE_URL = "https://paperswithcode.com/api/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AcademicTrendsSkill/1.0"})

    def fetch(self, topic: str) -> dict:
        """Fetch benchmark results for a research topic.

        Returns dict with benchmarks list and paper-to-benchmark mapping.
        """
        task_id = self._search_task(topic)
        if not task_id:
            return {"benchmarks": [], "paper_to_benchmark": {}}

        benchmarks = self._get_task_metrics(task_id)

        # Build paper_to_benchmark mapping
        paper_map = {}
        for bench in benchmarks:
            dataset_slug = bench.get("dataset_slug", "")
            for metric in bench.get("metrics", []):
                arxiv_id = metric.get("arxiv_id", "")
                if arxiv_id:
                    key = f"{dataset_slug}_{metric.get('shot', '')}"
                    if arxiv_id not in paper_map:
                        paper_map[arxiv_id] = []
                    if key not in paper_map[arxiv_id]:
                        paper_map[arxiv_id].append(key)

        return {
            "benchmarks": benchmarks,
            "paper_to_benchmark": paper_map
        }

    def _search_task(self, topic: str) -> Optional[str]:
        """Search for a task by topic name. Tries multiple query variations."""
        queries = [topic, topic.replace("few-shot", "few shot")]
        # Add shorter query variations for PWC which has more limited indexing
        short_topics = topic.split(" ")
        if len(short_topics) > 2:
            queries.append(" ".join(short_topics[:2]))

        for q in queries:
            try:
                params = {"q": q, "items_per_page": 5}
                resp = self.session.get(
                    f"{self.BASE_URL}/tasks/search",
                    params=params,
                    timeout=15
                )
                if resp.status_code != 200:
                    continue
                try:
                    data = resp.json()
                except ValueError:
                    continue
                results = data.get("results", [])
                if results:
                    return results[0].get("id")
            except (requests.RequestException, ValueError, KeyError):
                continue
        return None

    def _get_task_metrics(self, task_id: str) -> list[dict]:
        """Fetch benchmark metrics for a task."""
        benchmarks = []
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/tasks/{task_id}/metrics",
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            for result in data.get("results", []):
                dataset = result.get("dataset", {})
                metrics = result.get("metrics", [])

                # Group metrics by year
                yearly = {}
                for m in metrics:
                    year = m.get("year", 0)
                    if year not in yearly or m.get("value", 0) > yearly[year].get("value", 0):
                        yearly[year] = {
                            "year": year,
                            "best": m.get("value"),
                            "method": m.get("method_name", ""),
                            "paper_id": m.get("paper", ""),
                            "arxiv_id": self._extract_arxiv_id(m.get("paper_url", "")),
                        }

                # Determine saturation
                sorted_years = sorted(yearly.keys())
                saturation = "unknown"
                if len(sorted_years) >= 2:
                    recent = sorted_years[-2:]
                    if len(recent) == 2:
                        improvement = abs((yearly[recent[1]]["best"] or 0) - (yearly[recent[0]]["best"] or 0))
                        saturation = "approaching" if improvement < 5 else "active"

                benchmarks.append({
                    "dataset_slug": dataset.get("slug", ""),
                    "dataset_name": dataset.get("name", ""),
                    "task": result.get("task", ""),
                    "metrics": list(yearly.values()),
                    "saturation": saturation,
                })
        except (requests.RequestException, ValueError, KeyError):
            pass
        return benchmarks

    def _extract_arxiv_id(self, url: str) -> str:
        """Extract arXiv ID from a URL."""
        if not url:
            return ""
        import re
        match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", url)
        return match.group(1) if match else ""
