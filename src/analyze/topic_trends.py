from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "using",
    "this",
    "that",
    "into",
    "towards",
    "model",
    "models",
    "paper",
    "based",
    "learning",
}


def extract_top_terms(texts: list[str], top_k: int = 10) -> list[tuple[str, int]]:
    tokens: list[str] = []
    for t in texts:
        words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", t.lower())
        tokens.extend(w for w in words if w not in STOPWORDS)
    return Counter(tokens).most_common(top_k)
