from __future__ import annotations

import hashlib


def stable_id(*parts: str) -> str:
    raw = "||".join(p.strip().lower() for p in parts if p)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
