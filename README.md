# art-archive

전시 데이터 자동 수집기 (1차: 아트넷 → 노션 DB).

## 목적

매일 아트넷의 새 전시 정보를 자동 수집해 노션 DB(`exhibition_data_crawling`)에 적재한다.

## 운영자용 셋업 가이드

### 1. 노션 Integration 발급

1. https://www.notion.so/profile/integrations 접속
2. "+ New integration" 클릭
3. 이름: `art-archive` (자유), Workspace 선택, Type: Internal
4. 생성 후 **Internal Integration Token** 복사 (`secret_...`로 시작)
   - 이 토큰은 GitHub Actions가 노션에 쓰기 위해 사용. Claude의 노션 MCP 커넥터와는 별개

### 2. 노션 DB에 Integration 권한 부여

1. 노션에서 `exhibition_data_crawling` DB 페이지 열기
2. 우상단 `···` → `Connections` (또는 한국어로 `연결`)
3. 위에서 만든 `art-archive` Integration 선택해 추가

### 3. 노션 DB에 신규 필드 추가 (필수)

DB에 다음 두 필드가 없으면 추가한다.

- `출처 URL` — 타입 **URL**
- `수집 시각` — 타입 **Date**

또한 `개인/단체` SELECT에 `미상` 옵션이 없으면 추가.

### 4. NOTION_DB_ID 찾기

DB 페이지의 URL에서 추출:
```
https://www.notion.so/<workspace>/<DB_NAME>-e0f365a9159d4ac793bde494c4500f6a?v=...
                                              └────────── 이 32자가 DB_ID ──────────┘
```

### 5. GitHub Secret 등록

1. `art-archive` 레포 → Settings → Secrets and variables → Actions
2. `New repository secret` 두 개 추가:
   - `NOTION_TOKEN` — 1단계에서 복사한 토큰
   - `NOTION_DB_ID` — 4단계의 32자 ID (하이픈 없이)

### 6. 풀백필 1회 수동 실행

1. `art-archive` 레포 → Actions 탭
2. 좌측에서 `backfill` 워크플로 선택
3. 우측 상단 `Run workflow` 버튼 → `adapter: artnet` 입력 후 실행
4. 완료 후 노션 DB에 전시들이 적재됐는지 확인
5. 레포에 `chore(state): backfill ...` 커밋이 자동 생성됐는지 확인

### 7. 일일 자동 크롤 확인

`daily-crawl` 워크플로는 매일 03:00 KST(=18:00 UTC) 자동 실행.
첫 실행 다음 날 Actions 탭에서 결과 확인. 실패 시 GitHub의 기본 이메일 알림이 레포 소유자에게 자동 전송된다.

## 로컬 개발

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env 편집 — NOTION_TOKEN, NOTION_DB_ID 입력

pytest        # 모든 테스트 통과 확인
python -m src.run_daily --adapter artnet --dry-run   # 노션 적재 없이 URL만 출력
```

## 설계 문서

`docs/superpowers/specs/2026-05-04-exhibition-crawler-design.md`
