from __future__ import annotations

from pathlib import Path

from src.utils.io import ensure_parent


def write_monthly_markdown(monthly: dict, compare_notes: list[str], path: str | Path) -> None:
    lines: list[str] = []
    lines.append(f"# Monthly Research Flow - {monthly['month']}")
    lines.append("")
    lines.append(f"- Total papers: **{monthly['total_papers']}**")
    lines.append("")

    if compare_notes:
        lines.append("## Month-over-month")
        for note in compare_notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Category snapshots")
    for label, body in monthly.get("categories", {}).items():
        lines.append(f"### {label}")
        lines.append(f"- Count: {body.get('count', 0)}")
        terms = body.get("top_terms", [])[:8]
        if terms:
            pretty_terms = ", ".join(f"{x['term']}({x['count']})" for x in terms)
            lines.append(f"- Top terms: {pretty_terms}")
        titles = body.get("sample_titles", [])[:5]
        if titles:
            lines.append("- Sample papers:")
            for t in titles:
                lines.append(f"  - {t}")
        lines.append("")

    ensure_parent(path)
    Path(path).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
