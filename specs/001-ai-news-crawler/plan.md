# Implementation Plan: AI News Crawler

**Branch**: `001-ai-news-crawler` | **Date**: 2026-03-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-news-crawler/spec.md`

## Summary

AI 관련 기사, 논문, 기술 블로그를 HTML 스크래핑으로 크롤링하여 규칙 기반 중요도 점수로 정렬해 보여주는 웹 애플리케이션. `spec-kit/` 하위에 완전히 새로운 독립 프로젝트로 구현한다. 기존 `claude/` 디렉토리의 코드를 수정하지 않는다.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Jinja2, HTMX, Tailwind CSS, BeautifulSoup4, httpx, APScheduler, passlib[bcrypt]
**Storage**: SQLite (SQLAlchemy ORM, FTS5 전문검색)
**Testing**: pytest
**Target Platform**: 웹 브라우저 (반응형 UI)
**Project Type**: Web application (서버 사이드 렌더링 + HTMX)
**Performance Goals**: 게시물 목록 3초 이내, 검색 1초 이내 응답
**Constraints**: 한국어 콘텐츠 위주, 소스별 전용 HTML 파서, `claude/` 기존 코드 수정 금지
**Scale/Scope**: 초기 소스 10~20개, 일일 수집 100건 이하

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution은 아직 프로젝트별 원칙이 정의되지 않은 템플릿 상태이다. 기본 소프트웨어 엔지니어링 원칙 적용:

- **테스트**: pytest 기반 단위/통합 테스트 작성 ✅
- **보안**: 비밀번호 해싱(bcrypt), 세션 기반 인증, CSRF 보호 ✅
- **단순성**: 새 프로젝트, 불필요한 추상화 미도입 ✅
- **데이터 무결성**: 유니크 제약, 외래키, 트랜잭션 내 카운트 동기화 ✅

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-news-crawler/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api-endpoints.md # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (spec-kit/ 하위 새 프로젝트)

```text
spec-kit/
├── pyproject.toml          # 프로젝트 설정 + 의존성
├── .env.example            # 환경변수 템플릿
├── .gitignore              # Python 프로젝트용
├── main.py                 # FastAPI 앱 진입점
├── app/
│   ├── __init__.py
│   ├── config.py           # 환경변수, 설정
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py       # SQLAlchemy ORM 모델 (User, Article, Source, Like, Comment, Scrap, ScoringWeight, CrawlFailure)
│   │   └── session.py      # DB 엔진, 세션, 초기화
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py       # 회원가입, 로그인, 로그아웃
│   │   ├── dependencies.py # get_current_user, require_login, require_admin
│   │   ├── middleware.py   # UserContextMiddleware
│   │   └── password.py     # bcrypt 해싱
│   ├── api/
│   │   ├── __init__.py
│   │   ├── articles.py     # 게시물 목록/상세/검색
│   │   ├── likes.py        # 좋아요 토글
│   │   ├── comments.py     # 댓글 CRUD
│   │   ├── scraps.py       # 스크랩 토글/목록
│   │   └── admin.py        # 관리자 (소스/게시물/사용자/가중치/알림)
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── runner.py       # 크롤링 실행 오케스트레이션
│   │   ├── scheduler.py    # APScheduler 통합
│   │   ├── pipeline.py     # 크롤링 파이프라인 (중복 판별 + 스코어링)
│   │   ├── scorer.py       # 규칙 기반 중요도 점수 (DB 가중치 연동)
│   │   ├── dedup.py        # URL + 제목 유사도 중복 판별
│   │   ├── keywords.py     # AI 키워드 추출
│   │   └── parsers/        # 소스별 HTML 파서
│   │       ├── __init__.py
│   │       └── base.py     # 기본 파서 인터페이스
│   └── templates/
│       ├── base.html       # 기본 레이아웃 (사이드바, 네비게이션)
│       ├── feed.html       # 게시물 목록 (카테고리/국가 필터, 페이지네이션)
│       ├── article.html    # 게시물 상세 (좋아요, 댓글, 스크랩)
│       ├── search.html     # 검색 결과
│       ├── my_scraps.html  # 내 스크랩
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── admin/
│       │   ├── sources.html
│       │   ├── users.html
│       │   ├── weights.html
│       │   └── alerts.html
│       └── partials/
│           └── _comments.html  # 댓글 섹션 (HTMX partial)
├── scripts/
│   └── seed_admin.py       # 초기 관리자 계정 생성
├── config/
│   └── sources.json        # 초기 크롤링 소스 설정
└── tests/
    ├── __init__.py
    └── test_models.py      # 기본 모델 테스트
```

**Structure Decision**: `spec-kit/` 하위에 완전히 새로운 단일 프로젝트로 생성. SSR(Jinja2 + HTMX) 패턴이므로 별도 frontend 분리 불필요. `app/` 패키지로 모든 서버 코드를 구조화.

## Complexity Tracking

해당 없음 - Constitution 위반 사항 없음.
