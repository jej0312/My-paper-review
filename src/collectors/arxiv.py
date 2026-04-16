from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from src.normalize.clean_text import clip_text
from src.normalize.schema import Paper
from src.utils.hashing import stable_id


def _extract_primary_category(tags: list[str]) -> list[str]:
    out: list[str] = []
    for t in tags:
        if t.startswith("http"):
            continue
        if t and "." in t:
            out.append(t)
    return out


def collect_arxiv(max_results: int = 80) -> list[Paper]:
    """Collect latest cs papers using arXiv API (same universe as cs/new)."""
    params = urllib.parse.urlencode(
        {
            "search_query": "cat:cs.*",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "start": 0,
            "max_results": max_results,
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_bytes = resp.read()
    except Exception:
        return []

    root = ET.fromstring(xml_bytes)
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    papers: list[Paper] = []
    for entry in root.findall("a:entry", ns):
        title = clip_text(entry.findtext("a:title", default="", namespaces=ns), 512)
        abstract = clip_text(entry.findtext("a:summary", default="", namespaces=ns), 6000)
        link = entry.findtext("a:id", default="", namespaces=ns)
        published = entry.findtext("a:published", default="", namespaces=ns)
        comments = clip_text(entry.findtext("arxiv:comment", default="", namespaces=ns), 500)

        categories = [
            el.attrib.get("term", "") for el in entry.findall("a:category", ns) if el.attrib.get("term")
        ]
        authors = [
            a.findtext("a:name", default="", namespaces=ns)
            for a in entry.findall("a:author", ns)
            if a.findtext("a:name", default="", namespaces=ns)
        ]

        pdf_url = ""
        for l in entry.findall("a:link", ns):
            if l.attrib.get("title") == "pdf" or l.attrib.get("type") == "application/pdf":
                pdf_url = l.attrib.get("href", "")
                break

        arxiv_id = ""
        m = re.search(r"arxiv\.org/abs/([^v]+)", link)
        if m:
            arxiv_id = m.group(1)

        paper_id = stable_id("arxiv", arxiv_id or title)
        papers.append(
            Paper(
                paper_id=paper_id,
                source="arxiv",
                title=title,
                abstract=abstract,
                authors=authors,
                url=link,
                published_at=published,
                categories=_extract_primary_category(categories),
                meta={"arxiv_id": arxiv_id, "comments": comments, "pdf_url": pdf_url},
            )
        )
    return papers
