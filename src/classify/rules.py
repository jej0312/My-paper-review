from __future__ import annotations

from collections.abc import Iterable

DEFAULT_MAIN = "other"

_RULES: dict[str, list[str]] = {
    "llm": [
        "large language model",
        "llm",
        "prompt",
        "in-context",
        "instruction tuning",
        "agent",
        "rag",
    ],
    "knowledge_graph": [
        "knowledge graph",
        "kg",
        "graph rag",
        "ontology",
        "entity linking",
        "triple",
    ],
    "clinical_application": [
        "clinical",
        "ehr",
        "electronic health record",
        "radiology",
        "pathology",
        "biomedical",
        "patient",
        "diagnosis",
    ],
}


def classify_main_label(title: str, abstract: str) -> str:
    blob = f"{title} {abstract}".lower()
    for label, keywords in _RULES.items():
        if any(k in blob for k in keywords):
            return label
    return DEFAULT_MAIN


def pick_sub_labels(main_label: str, candidates: Iterable[str]) -> list[str]:
    cands = [c for c in candidates if c]
    if main_label == "llm":
        mapping = ["rag", "agents", "reasoning", "evaluation", "safety", "multimodal"]
    elif main_label == "knowledge_graph":
        mapping = ["graph_rag", "ontology", "graph_reasoning", "kg_completion", "retrieval"]
    elif main_label == "clinical_application":
        mapping = ["ehr", "radiology", "pathology", "biomedical_nlp", "patient_safety"]
    else:
        mapping = []
    found = [m for m in mapping if any(m.replace("_", " ") in c.lower() for c in cands)]
    return found[:3]
