# My-paper-review

arXiv `cs/new` 기반으로 LLM / Knowledge Graph / Clinical Application 연구 흐름을 자동 추적합니다.

## 운영 원칙

- **Weekly summary:** TF-IDF/키워드 기반 (**LLM 미사용**)
- **Monthly summary:** LLM 우선, 실패 시 fallback
- **Notion publish:** GitHub Actions Secrets 사용 (`NOTION_API_KEY`, `NOTION_DATABASE_ID`)
- **수집 소스:** 현재는 **arXiv 우선/단독 수집** (ICLR OpenReview/NeurIPS proceedings는 비활성)

## Commands

```bash
python -m src.main collect-daily --max-arxiv 80 --day 2026-04-16
python -m src.main collect-weekly --max-arxiv 120 --week-end-day 2026-04-16
python -m src.main build-monthly-report --month 2026-04
```

## Output

- Daily overview: `reports/daily/YYYY-MM-DD/overview.md`, `overview.json`
- Weekly overview: `reports/weekly/YYYY-Www/overview.md`, `overview.json`
- Monthly overview: `reports/monthly/YYYY-MM/overview.md`, `overview.json`
- Legacy monthly snapshots: `reports/YYYY-MM.md`, `reports/YYYY-MM.json`

## GitHub Actions

- `.github/workflows/daily_collect.yml`
  - daily collection + keyword summary (LLM 미사용)
  - **매일 미국 중부 시간 오전 7시** 실행
  - 별도 secret 불필요 (`OPENREVIEW_TOKEN` 미사용)
- `.github/workflows/weekly_collect.yml`
  - weekly collection + keyword summary (LLM 미사용)
  - 별도 secret 불필요 (`OPENREVIEW_TOKEN` 미사용)
- `.github/workflows/monthly_report.yml`
  - monthly LLM summary + Notion publish
  - secrets: `OPENAI_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID`

## 주요 구현 파일

- Daily/Weekly orchestration: `src/main.py` (`collect_daily`, `collect_weekly`)
- Weekly keyword summarizer: `src/analyze/keyword_summarizer.py`
- Monthly LLM summarizer: `src/analyze/llm_summarizer.py`
- Notion publish: `src/publish/notion_writer.py`
