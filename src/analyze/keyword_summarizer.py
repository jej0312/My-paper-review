from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from src.normalize.schema import Paper

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{2,}")
STOPWORDS = {
    "with",
    "from",
    "that",
    "this",
    "using",
    "based",
    "into",
    "towards",
    "their",
    "through",
    "than",
    "show",
    "shows",
    "study",
    "paper",
    "method",
    "approach",
    "results",
    "analysis",
    "task",
    "tasks",
    "model",
    "models",
    "dataset",
    "datasets",
}
PRIORITY_VENUES = ("ICLR", "NEURIPS", "NIPS", "IJCAI", "AAAI")


def _parse_iso(dt: str) -> datetime | None:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except ValueError:
        return None


def papers_in_window(papers: list[Paper], end_day: str, days: int = 7) -> list[Paper]:
    end = datetime.fromisoformat(end_day).replace(tzinfo=timezone.utc)
    start = end - timedelta(days=days - 1)
    out: list[Paper] = []
    for p in papers:
        dt = _parse_iso(p.published_at)
        if dt is None:
            continue
        if start.date() <= dt.date() <= end.date():
            out.append(p)
    return out


def _tokenize(text: str) -> list[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if t not in STOPWORDS and not t.isdigit()]


def _tfidf_keywords(papers: list[Paper], top_k: int = 12) -> list[dict[str, float]]:
    docs: list[list[str]] = []
    df: Counter[str] = Counter()

    for p in papers:
        toks = _tokenize(f"{p.title} {p.abstract}")
        if not toks:
            continue
        docs.append(toks)
        for tok in set(toks):
            df[tok] += 1

    if not docs:
        return []

    n_docs = len(docs)
    scores: defaultdict[str, float] = defaultdict(float)
    for toks in docs:
        tf = Counter(toks)
        length = max(len(toks), 1)
        for term, cnt in tf.items():
            idf = math.log((1 + n_docs) / (1 + df[term])) + 1.0
            scores[term] += (cnt / length) * idf

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [{"term": t, "score": round(s, 4)} for t, s in ranked]


def _venue_hit(p: Paper) -> str | None:
    hay = " ".join(
        [p.title or "", p.abstract or "", str(p.meta.get("comments", ""))]
    ).upper()
    for v in PRIORITY_VENUES:
        if v in hay:
            return v
    return None


def _line(label: str, text: str) -> str:
    return f"{label}: {text}"


def _paper_summary_lines(p: Paper) -> list[str]:
    venue = _venue_hit(p)
    comments = str(p.meta.get("comments", "")).strip() or "N/A"
    model = p.meta.get("model_hint") or "Not explicitly stated"
    data = p.meta.get("data_hint") or "Not explicitly stated"
    url = p.meta.get("pdf_url") or p.url
    return [
        _line("Title", p.title.strip()[:220]),
        _line("Contribution/Gap", p.abstract.strip().split(".")[0][:240] or "See abstract"),
        _line("Model/Architecture", str(model)[:220]),
        _line("Data", str(data)[:220]),
        _line("Comments", (f"{venue} signal | " if venue else "") + f"{comments[:160]} | {url}"),
    ]


def summarize_weekly_keyword(papers: list[Paper], period_label: str) -> dict:
    ordered = sorted(papers, key=lambda p: (_venue_hit(p) is None, p.published_at), reverse=False)
    venue_first = sorted(ordered, key=lambda p: _venue_hit(p) is None)

    paper_summaries = []
    for p in venue_first[:20]:
        paper_summaries.append(
            {
                "paper_id": p.paper_id,
                "lines": _paper_summary_lines(p),
                "venue_hint": _venue_hit(p),
            }
        )

    return {
        "period": period_label,
        "mode": "keyword",
        "top_keywords": _tfidf_keywords(papers),
        "paper_summaries": paper_summaries,
        "total_papers": len(papers),
    }
