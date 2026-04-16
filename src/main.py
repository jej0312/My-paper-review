from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from src.analyze.aggregate_month import build_monthly_reports, compare_monthly_reports
from src.analyze.llm_summarizer import summarize_papers
from src.classify.llm_classifier import classify_paper
from src.collectors.arxiv import collect_arxiv
from src.collectors.iclr_openreview import collect_iclr
from src.collectors.neurips_proceedings import collect_neurips
from src.normalize.schema import Paper
from src.publish.github_writer import write_monthly_markdown, write_overview_markdown
from src.utils.dates import month_key
from src.utils.io import append_jsonl, read_json, read_jsonl, write_json

PAPERS_STORE = "data/processed/papers.jsonl"
SEEN_IDS = "data/state/seen_ids.json"
CHECKPOINTS = "data/state/checkpoints.json"
REPORT_DIR = "reports"


def collect_daily(max_arxiv: int = 80, day: str | None = None) -> dict:
    seen_ids = set(read_json(SEEN_IDS, default=[]))

    papers: list[Paper] = []
    papers += collect_arxiv(max_results=max_arxiv)
    papers += collect_iclr()
    papers += collect_neurips()

    new_papers: list[Paper] = []
    new_rows: list[dict] = []
    added_ids: list[str] = []

    for p in papers:
        if p.paper_id in seen_ids:
            continue
        p = classify_paper(p)
        new_papers.append(p)
        new_rows.append(p.to_dict())
        added_ids.append(p.paper_id)

    inserted = append_jsonl(PAPERS_STORE, new_rows)
    write_json(SEEN_IDS, sorted(seen_ids.union(added_ids)))

    collect_day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_summary = summarize_papers(new_papers, period_label=f"daily:{collect_day}")
    overview_md = f"{REPORT_DIR}/daily/{collect_day}/overview.md"
    overview_json = f"{REPORT_DIR}/daily/{collect_day}/overview.json"

    write_overview_markdown(
        period_label=f"daily:{collect_day}",
        total_papers=inserted,
        summary_text=daily_summary["summary"],
        mode=daily_summary["mode"],
        path=overview_md,
    )
    write_json(
        overview_json,
        {
            "period": f"daily:{collect_day}",
            "total_papers": inserted,
            "summary": daily_summary["summary"],
            "mode": daily_summary["mode"],
            "model": daily_summary["model"],
        },
    )

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_daily_collect_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_inserted"] = inserted
    checkpoints["last_daily_overview"] = overview_md
    write_json(CHECKPOINTS, checkpoints)

    return {
        "collected_total": len(papers),
        "inserted": inserted,
        "daily_overview": overview_md,
        "summary_mode": daily_summary["mode"],
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

    month_papers = [p for p in rows if p.published_at and month_key(p.published_at) == target_month]
    monthly_summary = summarize_papers(month_papers, period_label=f"monthly:{target_month}")
    monthly_overview_md = f"{REPORT_DIR}/monthly/{target_month}/overview.md"
    monthly_overview_json = f"{REPORT_DIR}/monthly/{target_month}/overview.json"

    write_overview_markdown(
        period_label=f"monthly:{target_month}",
        total_papers=len(month_papers),
        summary_text=monthly_summary["summary"],
        mode=monthly_summary["mode"],
        path=monthly_overview_md,
    )
    write_json(
        monthly_overview_json,
        {
            "period": f"monthly:{target_month}",
            "total_papers": len(month_papers),
            "summary": monthly_summary["summary"],
            "mode": monthly_summary["mode"],
            "model": monthly_summary["model"],
        },
    )

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_monthly_report_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_report_month"] = target_month
    checkpoints["last_monthly_overview"] = monthly_overview_md
    write_json(CHECKPOINTS, checkpoints)

    return {
        "month": target_month,
        "total_papers": monthly.get("total_papers", 0),
        "monthly_overview": monthly_overview_md,
        "summary_mode": monthly_summary["mode"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research trend automation pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect-daily", help="Collect and normalize daily papers")
    p_collect.add_argument("--max-arxiv", type=int, default=80)
    p_collect.add_argument("--day", type=str, default=None, help="Override report day (YYYY-MM-DD)")

    p_month = sub.add_parser("build-monthly-report", help="Build monthly category flow report")
    p_month.add_argument("--month", type=str, default=datetime.now(timezone.utc).strftime("%Y-%m"))

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "collect-daily":
        result = collect_daily(max_arxiv=args.max_arxiv, day=args.day)
        print(result)
    elif args.cmd == "build-monthly-report":
        result = build_monthly_report(target_month=args.month)
        print(result)


if __name__ == "__main__":
    main()
