# My-paper-review

arXiv `cs/new` 기반으로 다음 3개 축의 연구 흐름을 월 단위로 추적하기 위한 자동화 뼈대입니다.

- LLM
- Knowledge Graph
- Clinical Application

추가 소스(확장 예정):
- ICLR (OpenReview)
- NeurIPS (Proceedings)

## Pipeline 구조

1. **Daily Collect (`collect-daily`)**
   - arXiv 최신 논문 수집
   - 정규화 스키마로 통합
   - 규칙 기반 카테고리 분류
   - 중복 제거 후 JSONL 저장
   - **당일 신규 수집분 전체를 LLM Agent로 요약** (`reports/daily/YYYY-MM-DD/overview.*`)

2. **Monthly Report (`build-monthly-report`)**
   - 월 기준 논문 집계
   - 카테고리별 핵심 키워드/샘플 타이틀 추출
   - 전월 대비 증감 비교
   - GitHub Wiki/문서 업로드용 마크다운 생성
   - **월 전체 수집분을 LLM Agent로 종합 요약** (`reports/monthly/YYYY-MM/overview.*`)

3. **Publish (stub)**
   - Notion 업데이트 함수 자리
   - 이메일 발송 함수 자리

## 디렉터리

- `src/collectors/`: 소스별 수집기
- `src/classify/`: 분류기
- `src/analyze/`: 월 집계/비교/LLM 요약
- `src/publish/`: 결과 발행
- `data/processed/`: 원천 결과 저장소(`papers.jsonl`)
- `data/state/`: 체크포인트/중복 ID 상태
- `reports/`: 월/일 리포트 산출물

## 로컬 실행

```bash
python -m src.main collect-daily --max-arxiv 120 --day 2026-04-16
python -m src.main build-monthly-report --month 2026-04
```

## LLM Agent 설정

- 환경변수 `OPENAI_API_KEY`가 있으면 OpenAI Responses API를 사용해 서술형 요약 생성
- `OPENAI_SUMMARY_MODEL`로 모델 지정 가능 (기본: `gpt-4.1-mini`)
- 키가 없거나 네트워크 실패 시 집계 기반 fallback 요약 자동 생성

## GitHub Actions

- `.github/workflows/daily_collect.yml`: 매일 23:00 UTC 실행
- `.github/workflows/monthly_report.yml`: 매월 1일 00:10 UTC 실행

## 다음 확장 포인트

- OpenReview/NeurIPS collector 실제 API 연동
- 카테고리별(LLM/KG/Clinical) 세부 리포트 자동 분리 생성 강화
- GitHub Wiki 자동 푸시 + Notion + 이메일 발송 자동화
