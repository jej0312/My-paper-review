from __future__ import annotations


def compare_counts(curr: dict[str, int], prev: dict[str, int]) -> list[str]:
    notes: list[str] = []
    all_keys = sorted(set(curr) | set(prev))
    for key in all_keys:
        c = curr.get(key, 0)
        p = prev.get(key, 0)
        delta = c - p
        if delta > 0:
            notes.append(f"{key}: +{delta} ({p} -> {c})")
        elif delta < 0:
            notes.append(f"{key}: {delta} ({p} -> {c})")
        else:
            notes.append(f"{key}: no change ({c})")
    return notes
