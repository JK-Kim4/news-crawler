# Research: AI News Crawler

**Date**: 2026-03-23 | **Branch**: `001-ai-news-crawler`

## Project Approach

### Decision: spec-kit/ 하위에 완전히 새로운 독립 프로젝트로 구현

**Rationale**: 사용자가 기존 `claude/` 코드베이스와 분리된 독립 프로젝트를 요청했다. 동일한 기술 스택(Python + FastAPI + SQLAlchemy)을 사용하되, 모든 코드를 처음부터 작성한다.

**Alternatives considered**:
- 기존 `claude/` 확장: 사용자가 명시적으로 거부
- 다른 프레임워크: 기존 프로젝트와의 일관성을 위해 동일 스택 유지

## Technical Decisions

### 1. 좋아요(Like) 기능 구현 방식

**Decision**: 별도 `likes` 테이블 + Article의 `like_count` 비정규화 필드

**Rationale**: 좋아요 수를 게시물 목록에서 매번 JOIN으로 COUNT하면 성능 저하. 비정규화 필드로 빠른 조회하고, 좋아요 토글 시 트랜잭션 내에서 카운트 동기화.

**Alternatives considered**:
- COUNT JOIN 방식: 단순하지만 목록 조회 시 성능 저하
- Redis 캐시: 현재 규모(100건/일)에서 과도한 인프라

### 2. 댓글(Comment) 구조

**Decision**: 단일 레벨 댓글 (대댓글 미지원)

**Rationale**: 스펙에서 대댓글/스레드 기능을 언급하지 않았으며, 초기 버전에서는 단순한 단일 레벨 댓글이 적합하다.

**Alternatives considered**:
- 중첩 댓글 (parent_id 참조): 스펙 범위 초과, 필요 시 추후 확장
- 스레드 기반: 과도한 복잡성

### 3. 스크랩(Scrap) 구현

**Decision**: 별도 `scraps` 테이블 (user_id + article_id 유니크 제약)

**Rationale**: 새 프로젝트이므로 기존 UserNote 테이블이 없다. 스크랩 전용 테이블로 깔끔하게 설계.

**Alternatives considered**:
- 범용 UserNote 테이블에 is_bookmarked 필드: 불필요한 복잡성

### 4. 중복 게시물 판별 - 제목 유사도

**Decision**: Python `difflib.SequenceMatcher` 사용, 유사도 임계값 0.85

**Rationale**: 외부 의존성 없이 표준 라이브러리로 구현 가능하며, 100건/일 규모에서 충분한 성능.

**Alternatives considered**:
- FuzzyWuzzy/RapidFuzz: 외부 의존성 추가, 현재 규모에서 불필요
- 코사인 유사도 (TF-IDF): 과도한 복잡성

### 5. 중요도 가중치 관리

**Decision**: `scoring_weights` 테이블에 가중치 저장, 관리자 UI에서 조정 가능

**Rationale**: 가중치를 DB에 저장하면 관리자가 런타임에 조정 가능. 재시작 불필요.

**Alternatives considered**:
- 환경변수/설정 파일: 변경 시 재시작 필요
- 하드코딩: 유연성 부족

### 6. 관리자 알림 방식 (크롤링 실패)

**Decision**: `crawl_failures` 테이블 + 관리자 대시보드에 알림 배지 표시

**Rationale**: 이메일 알림은 SMTP 설정에 의존적이므로, 우선 대시보드 내 알림으로 구현하고 이메일 알림은 선택적으로 확장.

**Alternatives considered**:
- 이메일 알림만: SMTP 설정 필수
- Slack/Webhook: 외부 서비스 의존성 추가

### 7. 인증 방식

**Decision**: 세션 기반 인증 (Starlette SessionMiddleware) + bcrypt 비밀번호 해싱. 이메일 인증은 초기 버전에서 생략.

**Rationale**: SSR(서버 사이드 렌더링) + HTMX 앱에서는 세션 기반이 가장 자연스럽다. JWT는 SPA에 적합하지만 이 프로젝트에는 과도.

**Alternatives considered**:
- JWT 토큰: SPA 앱에 적합, SSR에는 불필요한 복잡성
- OAuth2: 초기 버전에서는 과도

### 8. 전문 검색

**Decision**: SQLite FTS5 (trigram tokenizer)

**Rationale**: SQLite 내장 기능으로 별도 인프라 없이 한국어 포함 전문 검색 가능.

**Alternatives considered**:
- Elasticsearch: 현재 규모에서 과도한 인프라
- LIKE 검색: 성능 부족
