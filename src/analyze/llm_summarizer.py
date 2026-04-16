from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import Counter

from src.normalize.schema import Paper

OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


def _build_context_rows(papers: list[Paper], max_items: int = 120) -> list[dict]:
    rows: list[dict] = []
    for p in papers[:max_items]:
        rows.append(
            {
                "title": p.title,
                "abstract": p.abstract[:900],
                "main_label": p.main_label,
                "sub_labels": p.sub_labels,
                "source": p.source,
                "published_at": p.published_at,
                "url": p.url,
            }
        )
    return rows


def _fallback_summary(papers: list[Paper], period_label: str) -> str:
    if not papers:
        return f"{period_label}에 수집된 논문이 없어 요약을 생성하지 못했습니다."

    label_counter = Counter(p.main_label for p in papers)
    source_counter = Counter(p.source for p in papers)
    sub_counter = Counter(s for p in papers for s in p.sub_labels)

    top_labels = ", ".join(f"{k}:{v}" for k, v in label_counter.most_common(3)) or "N/A"
    top_sources = ", ".join(f"{k}:{v}" for k, v in source_counter.most_common(3)) or "N/A"
    top_subs = ", ".join(f"{k}:{v}" for k, v in sub_counter.most_common(8)) or "N/A"

    return (
        f"{period_label} 전체 수집 논문 {len(papers)}편을 기준으로 자동 요약했습니다.\n"
        f"- 카테고리 분포: {top_labels}\n"
        f"- 수집 소스 분포: {top_sources}\n"
        f"- 자주 등장한 하위 주제: {top_subs}\n"
        "- 환경 설정(OPENAI_API_KEY)이 준비되면 LLM 기반 서술형 요약으로 자동 전환됩니다."
    )


def summarize_papers(papers: list[Paper], period_label: str) -> dict:
    """
    Summarize a full paper batch. Uses OpenAI Responses API when key exists,
    otherwise falls back to a deterministic aggregate summary.
    """
    if not papers:
        return {
            "mode": "fallback",
            "model": None,
            "summary": _fallback_summary(papers, period_label),
        }

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_SUMMARY_MODEL", DEFAULT_MODEL)

    if not api_key:
        return {
            "mode": "fallback",
            "model": None,
            "summary": _fallback_summary(papers, period_label),
        }

    prompt = (
        "당신은 연구 트렌드 분석가입니다. 입력된 논문 묶음 전체를 바탕으로 한국어 요약을 작성하세요. "
        "출력 형식:\n"
        "1) 이번 기간 핵심 흐름 5개 불릿\n"
        "2) 새롭게 부상한 주제 3개\n"
        "3) 실무 적용 시사점 3개\n"
        "4) 다음 기간 모니터링 포인트 3개\n"
        "과장 없이, 데이터에 근거한 표현만 사용하세요."
    )

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": "You are a precise research summarization assistant."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"기간: {period_label}"},
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_text",
                        "text": json.dumps(_build_context_rows(papers), ensure_ascii=False),
                    },
                ],
            },
        ],
    }

    req = urllib.request.Request(
        OPENAI_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body.get("output_text", "").strip()
        if not text:
            text = _fallback_summary(papers, period_label)
            mode = "fallback"
            model_name = None
        else:
            mode = "llm"
            model_name = model
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        text = _fallback_summary(papers, period_label)
        mode = "fallback"
        model_name = None

    return {
        "mode": mode,
        "model": model_name,
        "summary": text,
    }
