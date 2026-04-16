from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from src.analyze.aggregate_month import build_monthly_reports, compare_monthly_reports
from src.analyze.keyword_summarizer import papers_in_window, summarize_weekly_keyword
from src.analyze.llm_summarizer import summarize_monthly_papers
from src.classify.llm_classifier import classify_paper
from src.collectors.arxiv import collect_arxiv
from src.collectors.iclr_openreview import collect_iclr
from src.collectors.neurips_proceedings import collect_neurips
from src.normalize.schema import Paper
from src.publish.github_writer import write_monthly_markdown
from src.publish.notion_writer import publish_to_notion
from src.utils.dates import month_key
from src.utils.io import append_jsonl, ensure_parent, read_json, read_jsonl, write_json

PAPERS_STORE = "data/processed/papers.jsonl"
SEEN_IDS = "data/state/seen_ids.json"
CHECKPOINTS = "data/state/checkpoints.json"
REPORT_DIR = "reports"
DAILY_DIR = f"{REPORT_DIR}/daily"
WEEKLY_DIR = f"{REPORT_DIR}/weekly"
MONTHLY_DIR = f"{REPORT_DIR}/monthly"


def _collect_and_insert(max_arxiv: int) -> tuple[list[Paper], int]:
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
    return new_papers, inserted



def collect_daily(max_arxiv: int = 80, day: str | None = None) -> dict:
    _, inserted = _collect_and_insert(max_arxiv=max_arxiv)
    rows = [Paper.from_dict(r) for r in read_jsonl(PAPERS_STORE)]

    target_day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_papers = papers_in_window(rows, end_day=target_day, days=1)

    summary = summarize_weekly_keyword(day_papers, period_label=f"daily:{target_day}")
    daily_overview_json = f"{DAILY_DIR}/{target_day}/overview.json"
    daily_overview_md = f"{DAILY_DIR}/{target_day}/overview.md"

    write_json(daily_overview_json, summary)
    md_lines = [
        f"# Daily Overview - {target_day}",
        "",
        f"- Summary mode: **{summary['mode']}**",
        f"- Total papers in day: **{summary['total_papers']}**",
        "",
        "## Top TF-IDF keywords",
    ]
    for kw in summary.get("top_keywords", []):
        md_lines.append(f"- {kw['term']}: {kw['score']}")

    md_lines.extend(["", "## Per-paper summaries (<=5 lines each)"])
    for paper in summary.get("paper_summaries", []):
        md_lines.append("")
        for ln in paper["lines"]:
            md_lines.append(f"- {ln}")

    ensure_parent(daily_overview_md)
    with open(daily_overview_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_daily_collect_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_inserted"] = inserted
    checkpoints["last_daily_overview"] = daily_overview_md
    checkpoints["last_daily_overview_json"] = daily_overview_json
    write_json(CHECKPOINTS, checkpoints)

    return {
        "inserted": inserted,
        "day": target_day,
        "daily_overview": daily_overview_md,
        "summary_mode": summary["mode"],
    }

def collect_weekly(max_arxiv: int = 120, week_end_day: str | None = None) -> dict:
    _, inserted = _collect_and_insert(max_arxiv=max_arxiv)
    rows = [Paper.from_dict(r) for r in read_jsonl(PAPERS_STORE)]

    end_day = week_end_day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_papers = papers_in_window(rows, end_day=end_day, days=7)
    week_tag = datetime.fromisoformat(end_day).strftime("%Y-W%V")

    summary = summarize_weekly_keyword(week_papers, period_label=f"weekly:{week_tag}")
    weekly_overview_json = f"{WEEKLY_DIR}/{week_tag}/overview.json"
    weekly_overview_md = f"{WEEKLY_DIR}/{week_tag}/overview.md"

    write_json(weekly_overview_json, summary)
    md_lines = [
        f"# Weekly Overview - {week_tag}",
        "",
        f"- Summary mode: **{summary['mode']}**",
        f"- Total papers in window: **{summary['total_papers']}**",
        "",
        "## Top TF-IDF keywords",
    ]
    for kw in summary.get("top_keywords", []):
        md_lines.append(f"- {kw['term']}: {kw['score']}")

    md_lines.extend(["", "## Per-paper summaries (<=5 lines each)"])
    for paper in summary.get("paper_summaries", []):
        md_lines.append("")
        for ln in paper["lines"]:
            md_lines.append(f"- {ln}")

    # Keep plain md file for wiki readability.
    ensure_parent(weekly_overview_md)
    with open(weekly_overview_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_weekly_collect_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_inserted"] = inserted
    checkpoints["last_weekly_overview"] = weekly_overview_md
    checkpoints["last_weekly_overview_json"] = weekly_overview_json
    write_json(CHECKPOINTS, checkpoints)

    return {
        "inserted": inserted,
        "week": week_tag,
        "weekly_overview": weekly_overview_md,
        "summary_mode": summary["mode"],
    }


def _previous_month(month: str) -> str:
    dt = datetime.strptime(month + "-01", "%Y-%m-%d")
    prev = dt.replace(day=1) - timedelta(days=1)
    return prev.strftime("%Y-%m")


def build_monthly_report(target_month: str) -> dict:
    rows = [Paper.from_dict(r) for r in read_jsonl(PAPERS_STORE)]
    monthly = build_monthly_reports(rows, target_month)

    prev_month = _previous_month(target_month)
    prev_report_path = f"{REPORT_DIR}/{prev_month}.json"
    prev_report = read_json(prev_report_path, default={})
    compare_notes = compare_monthly_reports(monthly, prev_report) if prev_report else []

    legacy_json = f"{REPORT_DIR}/{target_month}.json"
    legacy_md = f"{REPORT_DIR}/{target_month}.md"
    write_json(legacy_json, monthly)
    write_monthly_markdown(monthly, compare_notes, legacy_md)

    month_papers = [p for p in rows if p.published_at and month_key(p.published_at) == target_month]
    monthly_summary = summarize_monthly_papers(month_papers, period_label=f"monthly:{target_month}")
    monthly_overview_md = f"{MONTHLY_DIR}/{target_month}/overview.md"
    monthly_overview_json = f"{MONTHLY_DIR}/{target_month}/overview.json"

    ensure_parent(monthly_overview_md)
    with open(monthly_overview_md, "w", encoding="utf-8") as f:
        f.write("# Monthly Overview\n\n")
        f.write(f"- Period: monthly:{target_month}\n")
        f.write(f"- Summary mode: {monthly_summary['mode']}\n\n")
        f.write(monthly_summary["summary"].strip() + "\n")

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

    notion_result = publish_to_notion(
        {
            "month": target_month,
            "summary_markdown": monthly_summary["summary"],
            "total_papers": len(month_papers),
            "mode": monthly_summary["mode"],
            "overview_path": monthly_overview_md,
        }
    )

    checkpoints = read_json(CHECKPOINTS, default={})
    checkpoints["last_monthly_report_utc"] = datetime.now(timezone.utc).isoformat()
    checkpoints["last_report_month"] = target_month
    checkpoints["last_monthly_overview"] = monthly_overview_md
    checkpoints["last_monthly_overview_json"] = monthly_overview_json
    checkpoints["last_legacy_monthly_md"] = legacy_md
    checkpoints["last_legacy_monthly_json"] = legacy_json
    checkpoints["last_notion_publish"] = notion_result
    write_json(CHECKPOINTS, checkpoints)

    return {
        "month": target_month,
        "total_papers": monthly.get("total_papers", 0),
        "monthly_overview": monthly_overview_md,
        "summary_mode": monthly_summary["mode"],
        "notion": notion_result,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research trend automation pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_daily = sub.add_parser("collect-daily", help="Collect and summarize daily papers (keyword mode)")
    p_daily.add_argument("--max-arxiv", type=int, default=80)
    p_daily.add_argument("--day", type=str, default=None, help="Target day (YYYY-MM-DD)")

    p_weekly = sub.add_parser("collect-weekly", help="Collect and summarize weekly papers")
    p_weekly.add_argument("--max-arxiv", type=int, default=120)
    p_weekly.add_argument("--week-end-day", type=str, default=None, help="Week end day (YYYY-MM-DD)")

    p_month = sub.add_parser("build-monthly-report", help="Build monthly category flow report")
    p_month.add_argument("--month", type=str, default=datetime.now(timezone.utc).strftime("%Y-%m"))

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "collect-daily":
        result = collect_daily(max_arxiv=args.max_arxiv, day=args.day)
        print(result)
    elif args.cmd == "collect-weekly":
        result = collect_weekly(max_arxiv=args.max_arxiv, week_end_day=args.week_end_day)
        print(result)
    elif args.cmd == "build-monthly-report":
        result = build_monthly_report(target_month=args.month)
        print(result)


if __name__ == "__main__":
    main()
