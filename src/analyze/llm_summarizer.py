from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import Counter

from src.normalize.schema import Paper

OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1-mini"


def _build_context_rows(papers: list[Paper], max_items: int = 180) -> list[dict]:
    rows: list[dict] = []
    for p in papers[:max_items]:
        rows.append(
            {
                "title": p.title,
                "abstract": p.abstract[:1200],
                "main_label": p.main_label,
                "source": p.source,
                "published_at": p.published_at,
                "comments": p.meta.get("comments", ""),
            }
        )
    return rows


def _fallback_monthly_summary(papers: list[Paper], period_label: str) -> str:
    if not papers:
        return (
            "1) 이번 기간 핵심 흐름 5개\n- No papers collected.\n"
            "2) 새롭게 부상한 주제 3개\n- N/A\n"
            "3) 실무 적용 시사점 3개\n- N/A\n"
            "4) 다음 기간 모니터링 포인트 3개\n- 데이터 수집 상태를 점검하세요."
        )

    label_counter = Counter(p.main_label for p in papers)
    source_counter = Counter(p.source for p in papers)
    top_labels = ", ".join(f"{k}({v})" for k, v in label_counter.most_common(5))
    top_sources = ", ".join(f"{k}({v})" for k, v in source_counter.most_common(3))

    return (
        "1) 이번 기간 핵심 흐름 5개\n"
        f"- 카테고리 분포: {top_labels}\n"
        "- LLM/KG/Clinical 중심 논문이 지속 유입됨\n"
        "- 방법론 논문과 응용 논문이 혼재\n"
        f"- 주요 소스 분포: {top_sources}\n"
        "- 세부 토픽은 월간 category report 참고\n\n"
        "2) 새롭게 부상한 주제 3개\n"
        "- 멀티모달 LLM 활용 증가 가능성\n"
        "- 그래프 추론과 생성모델 결합\n"
        "- 의료 도메인 안전성/평가 이슈\n\n"
        "3) 실무 적용 시사점 3개\n"
        "- 도메인별 데이터 거버넌스가 성능만큼 중요\n"
        "- 경량화/비용 효율 아키텍처 모니터링 필요\n"
        "- 평가 지표 표준화가 배포 속도를 좌우\n\n"
        "4) 다음 기간 모니터링 포인트 3개\n"
        "- 주요 학회(ICLR/NeurIPS/IJCAI/AAAI) 채택 추세\n"
        "- 공개 데이터/벤치마크 업데이트\n"
        "- 재현성 및 실제 운영 성능 보고"
    )


def summarize_monthly_papers(papers: list[Paper], period_label: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_SUMMARY_MODEL", DEFAULT_MODEL)

    if not api_key:
        return {"mode": "fallback", "model": None, "summary": _fallback_monthly_summary(papers, period_label)}

    prompt = (
        "You are a rigorous research trend analyst."
        " Return Korean markdown with exactly these sections and bullet counts:\n"
        "1) 이번 기간 핵심 흐름 5개\n"
        "2) 새롭게 부상한 주제 3개\n"
        "3) 실무 적용 시사점 3개\n"
        "4) 다음 기간 모니터링 포인트 3개\n"
        "Use only evidence from provided papers."
    )

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": "Be concise and evidence-based."}]},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"기간: {period_label}"},
                    {"type": "input_text", "text": prompt},
                    {"type": "input_text", "text": json.dumps(_build_context_rows(papers), ensure_ascii=False)},
                ],
            },
        ],
    }

    req = urllib.request.Request(
        OPENAI_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        text = body.get("output_text", "").strip()
        if not text:
            return {"mode": "fallback", "model": None, "summary": _fallback_monthly_summary(papers, period_label)}
        return {"mode": "llm", "model": model, "summary": text}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return {"mode": "fallback", "model": None, "summary": _fallback_monthly_summary(papers, period_label)}
