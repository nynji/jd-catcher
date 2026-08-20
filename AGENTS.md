# AGENTS.md

이 문서는 AI 코딩 에이전트가 이 저장소에서 작업할 때 따라야 할 가이드입니다.

---

## 1. 프로젝트 목적

**역량 기반 채용공고 매칭 서비스** — 직군 타이틀이 아니라 **JD 본문의 요구 역량 ↔ 내 역량**으로 공고를 매칭하는 채용공고 관리 서비스.

- 링커리어 인턴 공고를 크롤링·구조화하여 Supabase(PostgreSQL)에 저장
- 이력서/포트폴리오/경험에서 AI가 역량을 추출하고, SQL로 `MEMBER_SKILL ↔ POSTING_SKILL` 매칭 점수 계산
- 매칭률·이유 설명, 관심공고 상태 관리, 자소서 문항별 AI 초안 생성
- MVP는 단일 유저(`member_id=1` 고정), 로그인·결제·SNS 등은 후순위

**핵심 차별점:** 타이틀(직군 카테고리)을 무시하고, JD 본문의 실제 요구 역량으로 매칭한다.

---

## 2. Frontend 기술

| 항목 | 기술 |
|---|---|
| 프레임워크 | React 19 + TypeScript |
| 빌드 | Vite 8 |
| CSS | Tailwind CSS 4 (`@tailwindcss/vite` 플러그인) |
| API 호출 | 브라우저 `fetch` (별도 HTTP 클라이언트 라이브러리 없음) |
| 환경변수 | `VITE_API_BASE_URL` (`.env.example` 참고) |

### Frontend 폴더 구조

```
frontend/src/
  api/           # 백엔드 REST API 호출 함수
  components/    # 공통 UI 컴포넌트
  pages/         # Home, ResumePage, PostingPage, MatchPage, ApplicationPage
  types/         # TypeScript 타입 정의
  App.tsx
  main.tsx
  index.css
```

### 실행

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build      # tsc -b && vite build
```

---

## 3. Backend 기술

| 항목 | 기술 |
|---|---|
| 프레임워크 | Python + FastAPI |
| ORM | SQLAlchemy |
| 스키마 검증 | Pydantic / pydantic-settings |
| DB | Supabase (PostgreSQL), `psycopg2-binary` |
| AI | OpenAI API (GPT-4o) — 역량 추출·매칭 설명·자소서 초안 |
| 서버 | uvicorn |

### Crawler (별도 모듈)

- `crawler/` — Playwright 크롤링, GitHub Actions cron으로 실행
- FastAPI 앱을 거치지 않고 Supabase에 직접 적재
- 크롤러 의존성은 `crawler/requirements.txt`에만 추가

### 실행

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # 환경변수 설정
uvicorn app.main:app --reload --port 8000   # http://localhost:8000
```

---

## 4. Backend 기본 구조

```
backend/app/
  main.py              # FastAPI 앱 진입점, CORS, 라우터 등록
  config.py            # 환경변수 (Settings)
  database.py          # SQLAlchemy engine, SessionLocal, Base, get_db
  models/              # SQLAlchemy 테이블 모델 (ERD 9개 테이블)
  schemas/             # Pydantic 요청/응답 스키마
  routers/
    postings.py        # 공고 조회
    resume.py          # 이력 등록
    match.py           # 매칭 분석
    application.py     # 관심공고·자소서
  services/
    ai_extractor.py    # 이력 → 역량 추출 (OpenAI)
    matching.py        # SQL 매칭 점수 계산
    cover_letter.py    # 자소서 초안 생성 (OpenAI)
```

### 레이어 역할

- **routers/** — HTTP 요청/응답, 경로 정의. 비즈니스 로직은 services에 위임
- **services/** — AI 호출, SQL 매칭 등 핵심 로직
- **models/** — DB 테이블 정의 (SQLAlchemy)
- **schemas/** — API 입출력 타입 (Pydantic)
- **database.py** — DB 세션 의존성 (`get_db`)

새 API를 추가할 때는 `routers/`에 라우터 파일을 만들고, `main.py`에서 `app.include_router()`로 등록한다.

---

## 5. REST API 사용

Frontend ↔ Backend 통신은 **REST API**만 사용한다.

- Backend: FastAPI `@app.get`, `@app.post`, `@app.put`, `@app.patch`, `@app.delete`
- Frontend: `frontend/src/api/`에 fetch 함수를 모아 호출
- Base URL: `VITE_API_BASE_URL` (기본값 `http://localhost:8000`)
- 응답 형식: JSON
- CORS: Backend `main.py`에서 `http://localhost:5173` 허용

### 예시 (현재 구현)

```
GET /health  →  { "status": "ok" }
GET /        →  { "message": "역량 기반 채용공고 매칭 API" }
```

### API 추가 시 규칙

1. Backend `routers/` + `schemas/`에 엔드포인트·스키마 정의
2. Frontend `src/api/`에 대응 fetch 함수 추가
3. 필요하면 `src/types/`에 TypeScript 타입 추가
4. GraphQL, gRPC, WebSocket 등은 사용하지 않는다

---

## 6. 불필요한 Library 추가 금지

작업에 **실제로 필요한 경우에만** 의존성을 추가한다.

- Frontend: axios, react-query, zustand 등 — 요청 없이 추가하지 않음. 현재는 `fetch`로 충분
- Backend: requests, httpx 등 — FastAPI/OpenAI SDK 등 명시적 필요가 있을 때만
- UI 라이브러리(shadcn, MUI 등), 상태관리, 라우터(react-router) — 화면·기능 구현 시 필요 판단 후 추가

새 패키지 추가 전에 기존 스택으로 해결 가능한지 먼저 확인한다.

---

## 7. Secret을 코드에 직접 작성하지 않기

API 키, DB URL, service role key 등 **민감 정보는 코드·커밋에 포함하지 않는다.**

| Secret | 위치 |
|---|---|
| `DATABASE_URL` | `backend/.env`, GitHub Actions Secrets |
| `OPENAI_API_KEY` | `backend/.env`, `crawler/` 실행 환경, GitHub Actions Secrets |
| `VITE_API_BASE_URL` | `frontend/.env` (공개 URL만, 키 아님) |

- `.env` 파일은 `.gitignore`에 포함됨
- `.env.example`에는 placeholder만 작성 (`your-openai-api-key` 등)
- Crawler는 Supabase `service_role` key 사용 — 프론트엔드에 노출 금지
- `config.py`의 Settings는 환경변수에서 읽도록 유지

---

## 8. 기존 파일을 대량으로 삭제하지 않기

- Vite/React 보일러플레이트, 이미 만든 `pages/`, `api/`, `routers/` 스켈레톤 등 **기존 파일을 무분별하게 삭제하지 않는다**
- 리팩터링이 필요하면 해당 파일만 수정하거나, 대체 파일을 만든 뒤 점진적으로 전환
- `node_modules/`, `dist/`, `__pycache__/` 등 빌드 산출물은 `.gitignore` 대상이며, 소스 코드 삭제와 구분

---

## 9. 큰 변경 전에 계획 먼저 설명하기

다음에 해당하면 **구현 전에 변경 범위·접근 방식을 먼저 설명**한다.

- ERD 테이블 추가/변경, 마이그레이션
- 새 router·service·페이지를 여러 개 한꺼번에 추가
- 폴더 구조 변경, 기술 스택 교체
- Crawler 파이프라인 전체 구현
- 매칭 SQL 로직, AI 프롬프트 설계

작은 수정(오타, 단일 엔드포인트 추가, 스타일 조정)은 바로 진행해도 된다.

---

## 10. 구현 후 Build 또는 테스트하기

코드 변경 후 **반드시 실행 가능 여부를 확인**한다.

### Frontend

```bash
cd frontend
npm run build          # TypeScript + Vite 빌드
# 또는 npm run dev 로 dev server 기동 확인
```

### Backend

```bash
cd backend
uvicorn app.main:app --port 8000
# GET http://localhost:8000/health → {"status":"ok"}
```

### Crawler (해당 작업 시)

```bash
cd crawler
python run.py          # 또는 개별 스크립트 실행
```

실행 실패 시 오류를 숨기지 말고 사용자에게 알린다.

---

## 11. 변경한 파일을 작업 마지막에 설명하기

작업을 마칠 때 **변경·생성한 파일 목록과 요약**을 응답 마지막에 포함한다.

### 형식 예시

```
## 변경 파일

| 파일 | 변경 내용 |
|---|---|
| backend/app/routers/postings.py | 공고 목록 GET API 추가 |
| frontend/src/api/client.ts | fetchPostings() 추가 |
| frontend/src/pages/PostingPage.tsx | 공고 목록 UI 연동 |
```

- 새로 만든 파일, 수정한 파일, 설정 변경(`package.json`, `requirements.txt` 등)을 구분
- 사용자가 리뷰·커밋하기 쉽도록 **무엇을 왜 바꿨는지** 한 줄로 설명

---

## 참고: 모노레포 루트 구조

```
project-root/
  backend/               # FastAPI
  frontend/              # React + Vite + TypeScript
  crawler/               # Playwright 크롤링 (GitHub Actions)
  .github/workflows/     # crawl.yml (cron)
  README.md
  AGENTS.md              # 이 파일
```

## 참고: 데이터 모델 (ERD 요약)

9개 테이블: `MEMBER`, `MEMBER_RESUME`, `MEMBER_SKILL`, `JOB_POSTING`, `SUBMISSION_REQUIREMENT`, `POSTING_ROLE`, `POSTING_SKILL`, `COVER_LETTER_QUESTION`, `APPLICATION`, `COVER_LETTER_DRAFT`

매칭 단위는 **세부 직무(`POSTING_ROLE`)**. `MEMBER_SKILL ↔ POSTING_SKILL` SQL 조인으로 점수 계산, OpenAI는 역량 추출(입력)과 이유 설명·자소서 초안(출력)에 사용.
