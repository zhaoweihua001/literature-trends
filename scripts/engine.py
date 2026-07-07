#!/usr/bin/env python3
"""Academic Literature Trend Analyzer Engine.

Usage:
    python scripts/engine.py --topic "few-shot image classification" \
        --categories cs.CV cs.LG --years 2023 2026 --max-results 200

Outputs structured JSON to stdout for Claude to analyze.
"""
import sys
import os
import json
import argparse
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix Windows stdout encoding for Unicode (emojis, non-ASCII)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

# Ensure engine package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.fetchers.arxiv import ArxivFetcher
from engine.fetchers.semanticscholar import SemanticScholarFetcher
from engine.fetchers.crossref import CrossRefFetcher
from engine.fetchers.paperswithcode import PapersWithCodeFetcher
from engine.fetchers.dblp import DBLPFetcher
from engine.merge import merge_papers
from engine.classify import classify_all, build_category_stats
from engine.output import build_output, build_keyword_trends


def parse_args():
    parser = argparse.ArgumentParser(description="Academic Literature Trend Analyzer")
    parser.add_argument("--topic", help="Research topic to analyze")
    parser.add_argument("--categories", nargs="+", default=["cs.CV"],
                        help="arXiv categories to search")
    parser.add_argument("--years", nargs=2, type=int, default=[2023, 2026],
                        help="Year range (start end)")
    parser.add_argument("--max-results", type=int, default=100,
                        help="Max papers to fetch from arXiv")
    parser.add_argument("--ss-api-key", default=None,
                        help="Semantic Scholar API key")
    parser.add_argument("--save-dir", default=None,
                        help="Directory to save raw results")
    parser.add_argument("--doctor", action="store_true",
                        help="Run diagnostic checks on all data sources")
    return parser.parse_args()


def doctor():
    """Diagnose all data sources and print health report."""
    results = []

    # 1. Python version
    py_ok = sys.version_info >= (3, 12)
    results.append({
        "name": "Python",
        "status": "🟢" if py_ok else "🔴",
        "detail": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "fix": "Install Python 3.12+ (winget install Python.Python.3.12)" if not py_ok else None,
    })

    # 2. requests
    try:
        import requests
        results.append({
            "name": "requests",
            "status": "🟢",
            "detail": f"requests {requests.__version__}",
            "fix": None,
        })
    except ImportError:
        results.append({
            "name": "requests",
            "status": "🔴",
            "detail": "not installed",
            "fix": "pip install -r requirements.txt",
        })

    # 3. arXiv API
    try:
        import requests as req
        r = req.get("http://export.arxiv.org/api/query",
                     params={"search_query": "all:test", "max_results": 1},
                     timeout=10)
        arxiv_ok = r.status_code == 200
        results.append({
            "name": "arXiv API",
            "status": "🟢" if arxiv_ok else "🔴",
            "detail": f"HTTP {r.status_code}" if not arxiv_ok else "Connected",
            "fix": "Check network connectivity" if not arxiv_ok else None,
        })
    except Exception as e:
        results.append({
            "name": "arXiv API",
            "status": "🔴",
            "detail": str(e)[:60],
            "fix": "Check network connectivity",
        })

    # 4. Semantic Scholar
    ss_key = os.environ.get("SS_API_KEY") or None
    try:
        import requests as req
        headers = {"User-Agent": "AcademicTrendsSkill/1.0"}
        if ss_key:
            headers["x-api-key"] = ss_key
        r = req.get("https://api.semanticscholar.org/graph/v1/paper/ArXiv:2303.12345",
                     params={"fields": "title,year"},
                     headers=headers, timeout=10)
        if r.status_code == 429:
            results.append({
                "name": "Semantic Scholar",
                "status": "🟡",
                "detail": "Rate limited (429)",
                "fix": "Add SS_API_KEY to .env or wait 1 minute",
            })
        elif r.status_code == 200:
            results.append({
                "name": "Semantic Scholar",
                "status": "🟢",
                "detail": f"OK (API Key: {'✅' if ss_key else '❌'})",
                "fix": None if ss_key else "Recommended: apply for free key at https://www.semanticscholar.org/product/api",
            })
        else:
            results.append({
                "name": "Semantic Scholar",
                "status": "🟡",
                "detail": f"HTTP {r.status_code}",
                "fix": "Check network or API status",
            })
    except Exception as e:
        results.append({
            "name": "Semantic Scholar",
            "status": "🔴",
            "detail": str(e)[:60],
            "fix": "Check network connectivity",
        })

    # 5. CrossRef
    try:
        import requests as req
        r = req.get("https://api.crossref.org/works/10.1109/CVPR.2024.12345",
                     params={"mailto": "user@example.com"},
                     timeout=10)
        cr_ok = r.status_code in (200, 404)  # 404 means API works, DOI just not found
        results.append({
            "name": "CrossRef",
            "status": "🟢" if cr_ok else "🔴",
            "detail": f"HTTP {r.status_code}" if not cr_ok else "OK",
            "fix": None,
        })
    except Exception as e:
        results.append({
            "name": "CrossRef",
            "status": "🔴",
            "detail": str(e)[:60],
            "fix": "Check network connectivity",
        })

    # 6. Papers With Code
    try:
        import requests as req
        r = req.get("https://paperswithcode.com/api/v1/tasks/search",
                     params={"q": "few-shot", "items_per_page": 1},
                     timeout=10)
        pwc_ok = r.status_code == 200
        results.append({
            "name": "Papers With Code",
            "status": "🟢" if pwc_ok else "🔴",
            "detail": f"HTTP {r.status_code}" if not pwc_ok else "OK",
            "fix": None,
        })
    except Exception as e:
        results.append({
            "name": "Papers With Code",
            "status": "🔴",
            "detail": str(e)[:60],
            "fix": "Check network connectivity",
        })

    # 7. DBLP
    try:
        import requests as req
        r = req.get("https://dblp.org/search/publ/api",
                     params={"q": "few-shot", "format": "json", "hits": 1},
                     timeout=10)
        dblp_ok = r.status_code == 200
        results.append({
            "name": "DBLP",
            "status": "🟢" if dblp_ok else "🔴",
            "detail": f"HTTP {r.status_code}" if not dblp_ok else "OK",
            "fix": None,
        })
    except Exception as e:
        results.append({
            "name": "DBLP",
            "status": "🔴",
            "detail": str(e)[:60],
            "fix": "Check network connectivity",
        })

    # 8. Firecrawl MCP
    fc_key = os.environ.get("FIRECRAWL_API_KEY")
    # Check .claude.json as well
    claude_cfg_path = os.path.expanduser("~/.claude.json")
    try:
        if not fc_key:
            with open(claude_cfg_path, encoding="utf-8", errors="replace") as f:
                cfg = json.load(f)
            proj = cfg.get("projects", {}).get("D:/mg/skill/literature-trends", {})
            mcp = proj.get("mcpServers", {})
            fc = mcp.get("firecrawl", {})
            fc_key = fc.get("env", {}).get("FIRECRAWL_API_KEY", "")
    except: pass

    results.append({
        "name": "Firecrawl MCP",
        "status": "🟢" if fc_key else "🟡",
        "detail": "API Key: ✅" if fc_key else "API Key: ❌",
        "fix": None if fc_key else "Register at https://www.firecrawl.dev/ and add API Key",
    })

    # 9. CCF Ranking file
    ccf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "engine", "ccf_rankings.py")
    ccf_ok = os.path.exists(ccf_path)
    results.append({
        "name": "CCF Rankings",
        "status": "🟢" if ccf_ok else "🔴",
        "detail": f"{'Found' if ccf_ok else 'Missing'}: {len(open(ccf_path, encoding='utf-8').readlines()) if ccf_ok else ''} lines" if ccf_ok else "Not found",
        "fix": None if ccf_ok else "Re-clone repository",
    })

    # Print report
    print(json.dumps({
        "doctor": True,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform": sys.platform,
        "checks": results,
        "summary": {
            "total": len(results),
            "green": sum(1 for r in results if r["status"] == "🟢"),
            "yellow": sum(1 for r in results if r["status"] == "🟡"),
            "red": sum(1 for r in results if r["status"] == "🔴"),
        }
    }, ensure_ascii=False, indent=2))


def main():
    args = parse_args()

    if args.doctor:
        doctor()
        return

    start_time = time.time()

    source_stats = {}
    warnings = []

    # Step 1: Fetch papers from arXiv
    print("[1/4] Fetching papers from arXiv...", file=sys.stderr)
    arxiv = ArxivFetcher()
    papers = arxiv.fetch(
        topic=args.topic,
        categories=args.categories,
        max_results=args.max_results,
        start_year=args.years[0],
        end_year=args.years[1]
    )
    source_stats["arxiv"] = {"count": len(papers)}
    print(f"  Found {len(papers)} papers from arXiv", file=sys.stderr)

    if not papers:
        output = {
            "meta": {
                "topic": args.topic,
                "years": f"{args.years[0]}-{args.years[1]}",
                "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_papers": 0,
                "sources_used": ["arxiv"],
                "source_stats": source_stats,
                "warnings": ["No papers found for this topic"]
            },
            "papers": [],
            "method_categories": {},
            "yearly_stats": [],
            "keyword_trends": {},
            "benchmark_trends": {},
            "high_impact_papers": [],
            "venue_distribution": {}
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # Step 2: Parallel enrichment
    print("[2/4] Enriching with citations, DOIs, benchmarks...", file=sys.stderr)
    arxiv_ids = [p["arxiv_id"] for p in papers if p.get("arxiv_id")]
    dois = [p["doi"] for p in papers if p.get("doi")]

    enrichment_results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        # Semantic Scholar
        futures["ss"] = executor.submit(
            lambda: SemanticScholarFetcher(api_key=args.ss_api_key).fetch_batch(arxiv_ids)
        )

        # CrossRef
        if dois:
            futures["crossref"] = executor.submit(
                lambda: CrossRefFetcher().fetch_by_dois(dois)
            )
        else:
            futures["crossref"] = executor.submit(lambda: {})

        # Papers With Code
        futures["pwc"] = executor.submit(
            lambda: PapersWithCodeFetcher().fetch(args.topic)
        )

        # DBLP
        futures["dblp"] = executor.submit(
            lambda: DBLPFetcher().fetch_venue_stats(papers[:50])
        )

        for name, future in futures.items():
            try:
                enrichment_results[name] = future.result()
            except Exception as e:
                warnings.append(f"{name} enrichment failed: {str(e)}")
                enrichment_results[name] = {} if name != "pwc" else {"benchmarks": [], "paper_to_benchmark": {}}

    ss_data = enrichment_results.get("ss", {})
    crossref_data = enrichment_results.get("crossref", {})
    pwc_data = enrichment_results.get("pwc", {"benchmarks": [], "paper_to_benchmark": {}})
    dblp_data = enrichment_results.get("dblp", {"venue_distribution": {}, "paper_venues": {}})

    source_stats["semantic_scholar"] = {"count": len(ss_data)}
    source_stats["crossref"] = {"count": len(crossref_data)}
    source_stats["papers_with_code"] = {"count": len(pwc_data.get("benchmarks", []))}
    source_stats["dblp"] = {"count": len(dblp_data.get("paper_venues", {}))}

    # Step 3: Merge and classify
    print("[3/4] Merging and classifying papers...", file=sys.stderr)
    enriched, filter_stats = merge_papers(
        papers, ss_data, crossref_data,
        pwc_data.get("paper_to_benchmark", {}),
        dblp_data.get("paper_venues", {})
    )

    # Log filtering stats
    print(f"  Venue filter: {filter_stats['total_raw']} raw -> "
          f"{filter_stats['no_venue_found']} no-venue, {filter_stats['not_ccf_a_b']} not-CCF-AB, "
          f"{filter_stats['journal_preprint']} journal-preprint -> "
          f"{filter_stats['ccf_a_conference']+filter_stats['ccf_b_conference']+filter_stats['ccf_a_journal']+filter_stats['ccf_b_journal']} kept "
          f"(A-conf:{filter_stats['ccf_a_conference']} B-conf:{filter_stats['ccf_b_conference']} "
          f"A-j:{filter_stats['ccf_a_journal']} B-j:{filter_stats['ccf_b_journal']})", file=sys.stderr)

    classified = classify_all(enriched)
    method_categories = build_category_stats(classified)

    # Build benchmark trends
    benchmark_trends = {}
    for bench in pwc_data.get("benchmarks", []):
        dataset = bench.get("dataset_slug", "unknown")
        yearly = {}
        for metric in bench.get("metrics", []):
            year = metric.get("year")
            if year:
                yearly[str(year)] = {"best": metric.get("best"), "method": metric.get("method", "")}
        if yearly:
            benchmark_trends[dataset] = yearly
            benchmark_trends[dataset]["saturation"] = bench.get("saturation", "unknown")

    # Build keyword trends
    keyword_trends = build_keyword_trends(classified)

    # Step 4: Assemble output
    print("[4/4] Assembling output...", file=sys.stderr)
    venue_distribution = dblp_data.get("venue_distribution", {})
    meta = {
        "topic": args.topic,
        "years": f"{args.years[0]}-{args.years[1]}",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_papers": len(classified),
        "sources_used": ["arxiv", "semantic_scholar", "crossref", "papers_with_code", "dblp"],
        "source_stats": source_stats,
        "elapsed_seconds": round(time.time() - start_time, 1),
    }
    if warnings:
        meta["warnings"] = warnings

    # Add CCF filtering stats to meta
    meta["filter_stats"] = filter_stats

    output = build_output(classified, meta, method_categories, keyword_trends, benchmark_trends, venue_distribution)

    # Print to stdout (for Claude to read)
    print(json.dumps(output, ensure_ascii=False, indent=2))

    # Save to file if requested
    if args.save_dir:
        os.makedirs(args.save_dir, exist_ok=True)
        meta_file = os.path.join(args.save_dir, "meta.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        papers_file = os.path.join(args.save_dir, "papers.json")
        with open(papers_file, "w", encoding="utf-8") as f:
            json.dump(classified, f, ensure_ascii=False, indent=2)

        analysis = {
            "method_categories": method_categories,
            "yearly_stats": output["yearly_stats"],
            "keyword_trends": output["keyword_trends"],
            "benchmark_trends": output["benchmark_trends"],
            "high_impact_papers": output["high_impact_papers"],
            "venue_distribution": output["venue_distribution"],
        }
        analysis_file = os.path.join(args.save_dir, "analysis.json")
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        print(f"[save] Saved meta to {meta_file}", file=sys.stderr)
        print(f"[save] Saved papers to {papers_file}", file=sys.stderr)
        print(f"[save] Saved analysis to {analysis_file}", file=sys.stderr)

    print(f"✅ Engine complete in {meta['elapsed_seconds']}s — {len(classified)} papers processed", file=sys.stderr)


if __name__ == "__main__":
    main()
