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
    parser.add_argument("--topic", required=True, help="Research topic to analyze")
    parser.add_argument("--categories", nargs="+", default=["cs.CV"],
                        help="arXiv categories to search")
    parser.add_argument("--years", nargs=2, type=int, default=[2023, 2026],
                        help="Year range (start end)")
    parser.add_argument("--max-results", type=int, default=200,
                        help="Max papers to fetch from arXiv")
    parser.add_argument("--ss-api-key", default=None,
                        help="Semantic Scholar API key")
    parser.add_argument("--save-dir", default=None,
                        help="Directory to save raw results")
    return parser.parse_args()


def main():
    args = parse_args()
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
    enriched = merge_papers(
        papers, ss_data, crossref_data,
        pwc_data.get("paper_to_benchmark", {}),
        dblp_data.get("paper_venues", {})
    )
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
