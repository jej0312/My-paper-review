from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def ensure_parent(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_yaml(path: str | Path, default: Any = None) -> Any:
    """Best-effort YAML loader. Falls back to default if PyYAML is unavailable."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        import yaml  # type: ignore
    except Exception:
        return default

    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def write_yaml(path: str | Path, data: Any) -> None:
    ensure_parent(path)
    try:
        import yaml  # type: ignore
    except Exception:
        # Minimal fallback: write JSON-compatible text when YAML lib is absent.
        with Path(path).open("w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return

    with Path(path).open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any) -> None:
    ensure_parent(path)
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> int:
    ensure_parent(path)
    cnt = 0
    with Path(path).open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            cnt += 1
    return cnt
