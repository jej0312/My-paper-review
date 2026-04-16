from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def publish_to_notion(monthly: dict) -> dict:
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        return {
            "status": "skipped",
            "reason": "missing_secrets",
            "required": ["NOTION_API_KEY", "NOTION_DATABASE_ID"],
        }

    title = f"Monthly Research Report {monthly.get('month', '')}"
    content = monthly.get("summary_markdown", "").strip()[:1900]

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"Mode: {monthly.get('mode', 'unknown')}"}}]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content or "(empty summary)"}}]
                },
            },
        ],
    }

    req = urllib.request.Request(
        f"{NOTION_API_BASE}/pages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return {"status": "ok", "page_id": body.get("id")}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "failed", "reason": str(exc)}
