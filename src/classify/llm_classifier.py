from __future__ import annotations

from src.classify.rules import classify_main_label, pick_sub_labels
from src.normalize.schema import Paper


def classify_paper(paper: Paper) -> Paper:
    label = classify_main_label(paper.title, paper.abstract)
    sub = pick_sub_labels(label, [paper.title, paper.abstract] + paper.categories)
    paper.main_label = label
    paper.sub_labels = sub
    return paper
