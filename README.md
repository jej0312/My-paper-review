# My-paper-review

arXiv `cs/new` 기반으로 LLM / Knowledge Graph / Clinical Application 연구 흐름을 자동 추적합니다.

## 운영 원칙

- **Weekly summary:** TF-IDF/키워드 기반 (**LLM 미사용**)
- **Monthly summary:** LLM 우선, 실패 시 fallback
- **Notion publish:** GitHub Actions Secrets 사용 (`NOTION_API_KEY`, `NOTION_DATABASE_ID`)

## Commands

```bash
python -m src.main collect-weekly --max-arxiv 120 --week-end-day 2026-04-16
python -m src.main build-monthly-report --month 2026-04
```

## Output

- Weekly overview: `reports/weekly/YYYY-Www/overview.md`, `overview.json`
- Monthly overview: `reports/monthly/YYYY-MM/overview.md`, `overview.json`
- Legacy monthly snapshots: `reports/YYYY-MM.md`, `reports/YYYY-MM.json`

## GitHub Actions

- `.github/workflows/weekly_collect.yml`
  - weekly collection + keyword summary
  - `OPENAI_API_KEY` 불필요
- `.github/workflows/monthly_report.yml`
  - monthly LLM summary + Notion publish
  - secrets: `OPENAI_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID`

## 주요 구현 파일

- Weekly orchestration: `src/main.py` (`collect_weekly`)
- Weekly keyword summarizer: `src/analyze/keyword_summarizer.py`
- Monthly LLM summarizer: `src/analyze/llm_summarizer.py`
- Notion publish: `src/publish/notion_writer.py`
