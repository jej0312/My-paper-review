from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Paper:
    """Canonical paper schema used across collectors and analyzers."""

    paper_id: str
    source: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    url: str = ""
    published_at: str = ""  # ISO-8601 datetime
    categories: list[str] = field(default_factory=list)
    main_label: str = "other"
    sub_labels: list[str] = field(default_factory=list)
    summary: str = ""
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Paper":
        return cls(**data)
