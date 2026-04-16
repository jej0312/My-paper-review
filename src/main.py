from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from src.analyze.aggregate_month import build_monthly_reports, compare_monthly_reports
from src.classify.llm_classifier import classify_paper
from src.collectors.arxiv import collect_arxiv
from src.collectors.iclr_openreview import collect_iclr
from src.collectors.neurips_proceedings import collect_neurips
from src.normalize.schema import Paper
from src.publish.github_writer import write_monthly_markdown
from src.utils.io import append_jsonl, read_json, read_jsonl, write_json

PAPERS_STORE = "data/processed/papers.jsonl"
SEEN_IDS = "data/state/seen_ids.json"
CHECKPOINTS = "data/state/checkpoints.json"
REPORT_DIR = "reports"


def collect_daily(max_arxiv: int = 80) -> dict:
    seen_ids = set(read_json(SEEN_IDS, default=[]))

    papers: list[Paper] = []
    papers += collect_arxiv(max_results=max_arxiv)
    papers += collect_iclr()
    papers += collect_neurips()

    new_rows: list[dict] = []
    added_ids: list[str] = []

    for p in papers:
        if p.paper_id in seen_ids:
            continue
        p = classify_paper(p)
        new_rows.append(p.to_dict())
        added_ids.append(p.paper_id)

    inserted = append_jsonl(PAPERS_STORE, new_rows)
    write_json(SEEN_IDS, sorted(seen_ids.union(added_ids)))

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_daily_collect_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_inserted"] = inserted
    write_json(CHECKPOINTS, checkpoints)

    return {
        "collected_total": len(papers),
        "inserted": inserted,
    }


def _previous_month(month: str) -> str:
    dt = datetime.strptime(month + "-01", "%Y-%m-%d")
    prev = dt - timedelta(days=1)
    return prev.strftime("%Y-%m")


def build_monthly_report(target_month: str) -> dict:
    rows = [Paper.from_dict(r) for r in read_jsonl(PAPERS_STORE)]
    monthly = build_monthly_reports(rows, target_month)

    prev_month = _previous_month(target_month)
    prev_report_path = f"{REPORT_DIR}/{prev_month}.json"
    prev_report = read_json(prev_report_path, default={})

    compare_notes = compare_monthly_reports(monthly, prev_report) if prev_report else []

    write_json(f"{REPORT_DIR}/{target_month}.json", monthly)
    write_monthly_markdown(monthly, compare_notes, f"{REPORT_DIR}/{target_month}.md")

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_monthly_report_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_report_month"] = target_month
    write_json(CHECKPOINTS, checkpoints)

    return {"month": target_month, "total_papers": monthly.get("total_papers", 0)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research trend automation pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect-daily", help="Collect and normalize daily papers")
    p_collect.add_argument("--max-arxiv", type=int, default=80)

    p_month = sub.add_parser("build-monthly-report", help="Build monthly category flow report")
    p_month.add_argument("--month", type=str, default=datetime.now(timezone.utc).strftime("%Y-%m"))

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "collect-daily":
        result = collect_daily(max_arxiv=args.max_arxiv)
        print(result)
    elif args.cmd == "build-monthly-report":
        result = build_monthly_report(target_month=args.month)
        print(result)


if __name__ == "__main__":
    main()
