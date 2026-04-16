from __future__ import annotations

from collections import Counter, defaultdict

from src.analyze.month_compare import compare_counts
from src.analyze.topic_trends import extract_top_terms
from src.normalize.schema import Paper
from src.utils.dates import month_key


def build_monthly_reports(papers: list[Paper], target_month: str) -> dict:
    bucket = [p for p in papers if p.published_at and month_key(p.published_at) == target_month]

    by_label: dict[str, list[Paper]] = defaultdict(list)
    for p in bucket:
        by_label[p.main_label].append(p)

    monthly: dict = {
        "month": target_month,
        "total_papers": len(bucket),
        "categories": {},
    }

    for label, rows in sorted(by_label.items()):
        terms = extract_top_terms([f"{r.title} {r.abstract}" for r in rows], top_k=12)
        sub_counter = Counter(s for r in rows for s in r.sub_labels)
        monthly["categories"][label] = {
            "count": len(rows),
            "top_terms": [{"term": t, "count": c} for t, c in terms],
            "sub_labels": dict(sub_counter),
            "sample_titles": [r.title for r in rows[:8]],
        }
    return monthly


def compare_monthly_reports(curr: dict, prev: dict) -> list[str]:
    curr_counts = {k: v.get("count", 0) for k, v in curr.get("categories", {}).items()}
    prev_counts = {k: v.get("count", 0) for k, v in prev.get("categories", {}).items()}
    return compare_counts(curr_counts, prev_counts)
