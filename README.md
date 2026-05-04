# art-archive

전시 데이터 자동 수집기 (1차: 아트넷 → 노션 DB).

## 빠른 시작

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` 후 `.env`에 노션 토큰/DB ID 입력
4. `pytest` — 테스트 통과 확인
5. (운영) 풀백필 1회: GitHub Actions의 `backfill` 워크플로 수동 실행
6. (운영) 매일 03:00 KST에 `daily-crawl` 워크플로 자동 실행

## 운영자용 셋업 가이드

(Phase 7 완료 시점에 노션 Integration 발급, GitHub Secret 등록 등의 단계별 가이드를 추가)

## 설계 문서

`docs/superpowers/specs/2026-05-04-exhibition-crawler-design.md`
