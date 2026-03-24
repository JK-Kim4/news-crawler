# AI 인사이트 수집 및 요약 웹 서비스 실행 계획

## 1. 개요 (Overview)
본 문서는 AI 관련 최신 논문, 기술 기사, 기업 블로그를 자동으로 수집하고, 거대 언어 모델(LLM)을 활용해 핵심 내용을 요약하여 사용자에게 제공하는 웹 서비스 구축을 위한 실행 계획입니다.

## 2. 목표 (Goals)
*   **자동화:** 다양한 소스(arXiv, TechCrunch, 기업 블로그 등)에서 최신 AI 콘텐츠를 자동으로 수집합니다. **(국내 기술 블로그 및 한글 자료 최우선 수집)**
*   **유연성:** 크롤링 대상 사이트를 소스 코드 수정 없이 JSON 설정 파일로 동적 관리합니다.
*   **제어권:** 6시간 주기 자동 실행뿐만 아니라, 관리자가 필요 시 즉시 크롤링을 실행할 수 있는 기능을 제공합니다.
*   **효율성:** 긴 글을 읽지 않아도 핵심 내용을 파악할 수 있도록 AI 요약을 제공합니다.
*   **접근성:** 웹 인터페이스를 통해 쉽게 검색하고 열람할 수 있으며, 중요 소식은 알림으로 받아볼 수 있습니다.

## 3. 시스템 아키텍처 (Architecture)
### 3.1. 전체 구조
*   **소스 관리자 (Source Manager):** `sources.json` 설정 파일을 로드하여 크롤링 대상 URL 및 파싱 규칙을 동적으로 관리합니다.
*   **수집기 (Crawler/Scraper):** 주기적으로 대상 사이트를 방문하여 새로운 콘텐츠를 감지하고 본문을 추출합니다. (자동 스케줄링 + 수동 트리거 지원)
*   **처리 엔진 (Processing Engine):** 수집된 본문을 정제하고, LLM API(OpenAI, Anthropic 등)를 호출하여 요약문을 생성합니다.
*   **인증 서비스 (Auth Service):** 회원가입, 로그인, JWT 토큰 발급 및 관리자(Admin)/일반(User) 권한을 관리합니다.
*   **데이터베이스 (Database):** 콘텐츠, 사용자, 스크랩, 댓글 정보를 저장합니다.
*   **백엔드 API (Backend API):**
    *   **Admin API:** 크롤링 제어, 소스 관리, 사용자 관리.
    *   **Public API:** 콘텐츠 조회, 검색.
    *   **User API:** 스크랩, 댓글 작성/수정/삭제.
*   **프론트엔드 (Frontend):**
    *   **사용자 웹:** 콘텐츠 피드, 상세 보기, 마이페이지(스크랩), 댓글 UI.
    *   **관리자 대시보드:** 크롤링 상태 모니터링, 수동 실행 버튼, 통계 확인.
*   **알림 서비스 (Notification Service):** 새로운 요약 생성 및 키워드 알림.

### 3.2. 기술 스택 (Tech Stack)
*   **Backend:** Python (FastAPI 또는 Django)
*   **Auth:** JWT (JSON Web Token), OAuth2 (Google/GitHub Login)
*   **Database:** PostgreSQL (Relation: User-Bookmark-Content)
*   **Task Queue:** Celery 또는 Redis Queue (RQ) - 크롤링 및 요약 작업의 비동기 처리
*   **AI/LLM:** OpenAI GPT-4o 또는 Claude 3.5 Sonnet (요약 품질 우수)
*   **Frontend:** React 또는 Next.js (SEO 및 사용자 경험 고려)
*   **Infrastructure:** Docker, AWS/GCP (배포)

## 4. 데이터 모델 (Data Model Draft)

### SourceConfig (크롤링 소스 설정 - sources.json)
*   `name`: String (예: "Naver D2", "Kakao Tech")
*   `base_url`: String
*   `rss_url`: String (Optional)
*   `selector_title`: String (CSS Selector)
*   `selector_content`: String (CSS Selector)
*   `language`: String ("ko", "en") - **우선순위 로직에 활용**
*   `is_active`: Boolean

### Content (수집된 콘텐츠)
*   `id`: UUID
*   `source_type`: Enum (PAPER, BLOG, NEWS)
*   `source_name`: String (SourceConfig.name)
*   `title`: String
*   `original_url`: String (Unique)
*   `published_at`: DateTime
*   `author`: String
*   `summary`: Text (AI Generated)
*   `tags`: List[String] (AI Generated)
*   `raw_content`: Text (Optional, for processing)
*   `created_at`: DateTime

### User (사용자)
*   `id`: UUID
*   `username`: String
*   `email`: String
*   `password_hash`: String
*   `role`: Enum (ADMIN, USER)
*   `created_at`: DateTime

### Interaction (사용자 활동)
*   `Bookmark`: { `user_id`: UUID, `content_id`: UUID, `created_at`: DateTime }
*   `Comment`: { `id`: UUID, `user_id`: UUID, `content_id`: UUID, `content`: Text, `created_at`: DateTime }

## 5. 단계별 구현 계획 (Implementation Steps)

### Phase 1: 기본 인프라 및 동적 수집기 개발 (Core & Crawler)
1.  **프로젝트 설정:** Python 환경 설정, FastAPI/Django 프로젝트 생성.
2.  **데이터베이스 설계:** PostgreSQL 스키마 정의 (User, Content, Bookmark, Comment).
3.  **소스 관리 모듈:** `sources.json` 파싱 및 관리 로직 구현.
4.  **크롤러 구현 (Base):** `BeautifulSoup` 및 `Playwright` 기반 수집기 개발.
5.  **스케줄러/트리거:** `Celery Beat` 자동 실행 및 `/admin/crawl/run` API 구현.

### Phase 2: 사용자 인증 및 관리자 기능 (Auth & Admin)
1.  **인증 시스템:** JWT 기반 회원가입/로그인, OAuth2 연동.
2.  **권한 관리:** API 접근 제어 (Admin vs User).
3.  **관리자 대시보드 API:** 크롤링 상태 조회 및 제어 API 개발.

### Phase 3: AI 요약 및 콘텐츠 API (AI & Content)
1.  **LLM 연동:** OpenAI/Anthropic API 연동 및 프롬프트 최적화.
2.  **콘텐츠 API:** 목록 조회, 상세 조회, 검색, 필터링.
3.  **상호작용 API:** 스크랩(북마크) 추가/해제, 댓글 작성/삭제.

### Phase 4: 프론트엔드 개발 (Web UI)
1.  **사용자 페이지:** 메인 피드, 상세 페이지, 마이페이지(스크랩 모음).
2.  **관리자 페이지:** 별도 경로(`/admin`)로 접근, 크롤링 제어 및 통계 대시보드.
3.  **검색 및 알림 UI:** 검색창 및 알림 설정 화면 구현.

### Phase 4: 알림 및 고도화 (Notification & Polish)
1.  **알림 서비스:** 이메일(SMTP/SendGrid) 또는 슬랙 웹훅 연동.
2.  **사용자 설정:** 관심 키워드 및 알림 수신 설정 기능.
3.  **배포 및 테스트:** Docker Containerization 및 클라우드 배포.

## 6. 검증 계획 (Verification)
*   **크롤링 테스트:** 각 소스별로 데이터가 정상적으로 수집되는지 확인.
*   **요약 품질 평가:** 생성된 요약문이 원문의 핵심을 잘 담고 있는지 샘플링 검수.
*   **성능 테스트:** 다수의 문서가 동시에 수집될 때 시스템 부하 확인.

## 7. 다음 단계 (Next Steps)
*   사용자 피드백을 반영하여 수집 소스 확장.
*   벡터 데이터베이스 도입을 통한 의미 기반 검색(Semantic Search) 구현 고려.
