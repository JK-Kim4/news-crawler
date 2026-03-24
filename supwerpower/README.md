# AI 인사이트 허브

AI 관련 최신 논문, 기술 블로그, 뉴스를 자동 수집하고 LLM으로 요약하여 제공하는 웹 서비스입니다.

## 주요 기능

- **자동 크롤링** - 국내외 기술 블로그(Naver D2, Kakao Tech, Toss Tech 등), 논문(arXiv), 뉴스(TechCrunch) 자동 수집 (6시간 주기)
- **AI 요약** - Anthropic Claude API를 활용한 한국어 핵심 요약 및 태그 자동 추출
- **동적 소스 관리** - `sources.json` 기반으로 크롤링 대상을 코드 수정 없이 추가/변경
- **관리자 대시보드** - 크롤링 상태 모니터링, 수동 실행, 소스 CRUD
- **사용자 기능** - 회원가입/로그인(JWT), 북마크, 댓글, 검색

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy (async), SQLite, APScheduler |
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Auth | JWT (HS256), bcrypt |
| Crawler | httpx, BeautifulSoup4, feedparser |
| AI | Anthropic Claude API |
| Infra | Docker, Docker Compose |

## 프로젝트 구조

```
supwerpower/
├── backend/
│   ├── app/
│   │   ├── api/          # Auth, Content, Admin, User 라우터
│   │   ├── models/       # SQLAlchemy 모델 (User, Content, Bookmark, Comment)
│   │   ├── schemas/      # Pydantic v2 스키마
│   │   ├── services/     # Crawler, Summarizer, Scheduler, SourceManager
│   │   └── core/         # JWT 보안, FastAPI 의존성
│   ├── sources.json      # 크롤링 소스 설정
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   └── src/
│       ├── app/          # 페이지 (피드, 상세, 검색, 로그인, 관리자)
│       ├── components/   # 재사용 컴포넌트
│       └── lib/          # API 클라이언트, Auth Context, 타입
└── docker-compose.yml
```

## 실행 방법

### Backend

```bash
cd supwerpower/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

→ http://localhost:8000 (Swagger UI: http://localhost:8000/docs)

### Frontend

```bash
cd supwerpower/frontend
npm install
npm run dev
```

→ http://localhost:3000

### Docker Compose

```bash
cd supwerpower
docker compose up --build
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./news_crawler.db` | DB 연결 문자열 |
| `SECRET_KEY` | `dev-secret-key-change-in-production` | JWT 서명 키 |
| `ANTHROPIC_API_KEY` | - | Claude API 키 (없으면 mock 요약 사용) |
| `CORS_ORIGINS` | `*` | 허용 CORS 출처 |

## API 엔드포인트 (27개)

| 그룹 | 메서드 | 경로 | 설명 |
|------|--------|------|------|
| Auth | POST | `/api/auth/register` | 회원가입 |
| Auth | POST | `/api/auth/login` | 로그인 (JWT 발급) |
| Content | GET | `/api/contents/` | 콘텐츠 목록 (페이징, 필터) |
| Content | GET | `/api/contents/{id}` | 콘텐츠 상세 |
| Content | GET | `/api/contents/search` | 키워드 검색 |
| Admin | POST | `/api/admin/crawl/run` | 크롤링 즉시 실행 |
| Admin | GET | `/api/admin/crawl/status` | 크롤링 상태 조회 |
| Admin | GET | `/api/admin/sources` | 소스 목록 |
| Admin | POST | `/api/admin/sources` | 소스 추가 |
| Admin | PUT | `/api/admin/sources/{name}` | 소스 수정 |
| Admin | DELETE | `/api/admin/sources/{name}` | 소스 삭제 |
| Admin | GET | `/api/admin/stats` | 대시보드 통계 |
| User | GET | `/api/user/me` | 내 프로필 |
| User | GET | `/api/user/bookmarks` | 북마크 목록 |
| User | POST | `/api/user/bookmarks` | 북마크 추가 |
| User | DELETE | `/api/user/bookmarks/{content_id}` | 북마크 삭제 |
| User | POST | `/api/user/contents/{id}/comments` | 댓글 작성 |
| User | DELETE | `/api/user/comments/{id}` | 댓글 삭제 |
| User | GET | `/api/user/contents/{id}/comments` | 댓글 목록 |
