from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def clip_text(text: str, max_len: int = 4000) -> str:
    text = normalize_whitespace(text)
    return text[:max_len]
