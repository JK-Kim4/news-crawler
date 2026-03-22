# Tasks: AI News Crawler

**Input**: Design documents from `/specs/001-ai-news-crawler/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-endpoints.md
**Project Root**: `spec-kit/` (새 독립 프로젝트, `claude/` 수정 금지)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions (all relative to `spec-kit/`)

---

## Phase 1: Setup

**Purpose**: Create new project from scratch with all dependencies and base structure

- [x] T001 Create pyproject.toml with dependencies (FastAPI, SQLAlchemy, Jinja2, httpx, beautifulsoup4, apscheduler, passlib[bcrypt], python-dotenv, uvicorn, pytest) in spec-kit/pyproject.toml
- [x] T002 Create .env.example with SECRET_KEY and DATABASE_URL placeholders in spec-kit/.env.example
- [x] T003 Create .gitignore for Python project in spec-kit/.gitignore
- [x] T004 Create project directory structure with all __init__.py files per plan.md in spec-kit/app/
- [x] T005 Create app config module loading env vars (SECRET_KEY, DATABASE_URL) in spec-kit/app/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB models, session, auth system - MUST complete before any user story

- [x] T006 Create all SQLAlchemy ORM models (User, Source, Article, Scrap, Like, Comment, ScoringWeight, CrawlFailure) per data-model.md in spec-kit/app/db/models.py
- [x] T007 Create DB engine, session factory, init_db() with FTS5 setup and scoring_weights seed in spec-kit/app/db/session.py
- [x] T008 [P] Create bcrypt password hashing utilities (hash_password, verify_password) in spec-kit/app/auth/password.py
- [x] T009 [P] Create Jinja2 templates configuration with custom filters and globals in spec-kit/app/api/templates.py
- [x] T010 Create auth dependencies (get_current_user, require_login, require_admin, LoginRequired exception) in spec-kit/app/auth/dependencies.py
- [x] T011 Create UserContextMiddleware that loads user from session into request.state in spec-kit/app/auth/middleware.py
- [x] T012 Create auth router with GET/POST /auth/register, GET/POST /auth/login, POST /auth/logout with is_active check in spec-kit/app/auth/router.py
- [x] T013 Create login.html and register.html auth templates in spec-kit/app/templates/auth/login.html and spec-kit/app/templates/auth/register.html
- [x] T014 Create base.html layout template with sidebar navigation (feed, search, scraps, admin links) and Tailwind+HTMX in spec-kit/app/templates/base.html
- [x] T015 Create FastAPI app entry point with lifespan, middleware, all router registrations in spec-kit/main.py
- [x] T016 [P] Create admin seed script (admin@example.com / admin123) in spec-kit/scripts/seed_admin.py
- [x] T017 [P] Create initial sources.json config with sample Korean AI news sources in spec-kit/config/sources.json

**Checkpoint**: App starts, DB initializes, register/login works

---

## Phase 3: User Story 1 - AI 콘텐츠 탐색 및 중요도 기반 열람 (Priority: P1) MVP

**Goal**: 사용자가 크롤링된 AI 게시물을 중요도 순으로 열람하고, 카테고리 필터/검색/상세 보기를 사용할 수 있다.

**Independent Test**: 메인 페이지에서 게시물이 중요도 순으로 표시되고, 카테고리 필터와 검색이 동작하며, 게시물 클릭 시 상세 정보가 표시되는지 확인.

### Implementation for User Story 1

- [x] T018 [P] [US1] Create AI keyword extraction module (Korean AI terms list + matching) in spec-kit/app/crawler/keywords.py
- [x] T019 [P] [US1] Create URL + title similarity dedup module (difflib.SequenceMatcher, threshold 0.85) in spec-kit/app/crawler/dedup.py
- [x] T020 [P] [US1] Create rule-based scorer reading weights from DB (source_trust, recency, keyword, engagement) in spec-kit/app/crawler/scorer.py
- [x] T021 [US1] Create base parser interface and crawled item dataclass in spec-kit/app/crawler/parsers/base.py
- [x] T022 [US1] Create crawl pipeline (dedup check → keyword filter → score → save → FTS index) in spec-kit/app/crawler/pipeline.py
- [x] T023 [US1] Create crawl runner orchestrating all sources with error tracking in spec-kit/app/crawler/runner.py
- [x] T024 [US1] Create APScheduler integration for periodic crawling in spec-kit/app/crawler/scheduler.py
- [x] T025 [US1] Create source loader that syncs sources.json to DB on startup in spec-kit/app/crawler/loader.py
- [x] T026 [US1] Implement GET / (feed) with category/country filter, sort, pagination in spec-kit/app/api/articles.py
- [x] T027 [US1] Implement GET /search with FTS5 query and category filter in spec-kit/app/api/articles.py
- [x] T028 [US1] Implement GET /articles/{id} detail with score breakdown in spec-kit/app/api/articles.py
- [x] T029 [US1] Create feed.html template with category tabs, country tabs, sort, pagination, article cards in spec-kit/app/templates/feed.html
- [x] T030 [US1] Create search.html template with search input and results in spec-kit/app/templates/search.html
- [x] T031 [US1] Create article.html detail template with score breakdown, content, original link in spec-kit/app/templates/article.html

**Checkpoint**: US1 fully functional - article browsing with filters, search, detail page

---

## Phase 4: User Story 2 - 관리자 크롤링 소스 및 콘텐츠 관리 (Priority: P1)

**Goal**: 관리자가 소스 CRUD, 게시물 삭제/점수 조정, 사용자 관리, 가중치 조정, 크롤링 실패 알림을 사용.

**Independent Test**: 관리자 로그인 후 소스 추가/삭제, 게시물 점수 조정, 사용자 역할 변경, 가중치 조정이 동작하는지 확인.

### Implementation for User Story 2

- [x] T032 [US2] Implement admin source CRUD endpoints (GET/POST/PUT/DELETE /admin/sources, POST /admin/sources/{id}/crawl) in spec-kit/app/api/admin.py
- [x] T033 [US2] Implement admin article management (POST /admin/articles/{id}/delete soft-delete, POST /admin/articles/{id}/score) in spec-kit/app/api/admin.py
- [x] T034 [US2] Implement admin user management (GET /admin/users, POST /admin/users/{id}/role, POST /admin/users/{id}/active) with self-demotion prevention in spec-kit/app/api/admin.py
- [x] T035 [US2] Implement admin scoring weight endpoints (GET /admin/scoring-weights, POST /admin/scoring-weights/{key}) in spec-kit/app/api/admin.py
- [x] T036 [US2] Implement admin crawl failure endpoints (GET /admin/crawl-failures, GET /admin/crawl-failures/count, POST /admin/crawl-failures/{id}/resolve) in spec-kit/app/api/admin.py
- [x] T037 [P] [US2] Create admin/sources.html template with add form and source table in spec-kit/app/templates/admin/sources.html
- [x] T038 [P] [US2] Create admin/users.html template with role/active controls in spec-kit/app/templates/admin/users.html
- [x] T039 [P] [US2] Create admin/weights.html template with editable weight forms in spec-kit/app/templates/admin/weights.html
- [x] T040 [P] [US2] Create admin/alerts.html template with failure list and resolve action in spec-kit/app/templates/admin/alerts.html

**Checkpoint**: US2 fully functional - all admin management features operational

---

## Phase 5: User Story 6 - 사용자 회원가입 및 로그인 (Priority: P1)

**Goal**: is_active 체크 포함 인증, 비로그인 사용자 기능 제한 UI.

**Independent Test**: 회원가입/로그인 동작, 비활성화 사용자 로그인 거부, 비로그인 시 버튼 비활성화 확인.

### Implementation for User Story 6

- [x] T041 [US6] Add non-authenticated user UI gating - conditionally show/hide like, scrap, comment buttons with login prompts in spec-kit/app/templates/feed.html and spec-kit/app/templates/article.html

**Checkpoint**: US6 fully functional - auth with is_active check and UI gating

---

## Phase 6: User Story 3 - 게시물 스크랩 (Priority: P2)

**Goal**: 로그인 사용자가 스크랩 토글 및 내 스크랩 페이지 사용.

**Independent Test**: 스크랩 버튼 토글 동작, /my/scraps 페이지에서 스크랩 목록 최신순 표시 확인.

### Implementation for User Story 3

- [x] T042 [US3] Implement POST /articles/{id}/scrap toggle endpoint in spec-kit/app/api/scraps.py
- [x] T043 [US3] Implement GET /my/scraps paginated list endpoint in spec-kit/app/api/scraps.py
- [x] T044 [US3] Create my_scraps.html template with paginated list and unscrap buttons in spec-kit/app/templates/my_scraps.html
- [x] T045 [US3] Add scrap toggle button (HTMX) to article cards in feed.html and article.html in spec-kit/app/templates/feed.html and spec-kit/app/templates/article.html

**Checkpoint**: US3 fully functional - scrap toggle and scrap list page

---

## Phase 7: User Story 4 - 게시물 좋아요 (Priority: P2)

**Goal**: 로그인 사용자가 좋아요 토글, 좋아요 수 실시간 표시.

**Independent Test**: 좋아요 버튼 토글 시 카운트 증감, 비로그인 시 로그인 유도 확인.

### Implementation for User Story 4

- [x] T046 [US4] Implement POST /articles/{id}/like toggle endpoint with like_count sync in spec-kit/app/api/likes.py
- [x] T047 [US4] Add like toggle button (HTMX) with count to feed.html and article.html in spec-kit/app/templates/feed.html and spec-kit/app/templates/article.html
- [x] T048 [US4] Add user_liked status to article enrichment for active button state in spec-kit/app/api/articles.py

**Checkpoint**: US4 fully functional - like toggle with count display

---

## Phase 8: User Story 5 - 게시물 댓글 (Priority: P3)

**Goal**: 로그인 사용자 댓글 CRUD, 관리자 모든 댓글 삭제.

**Independent Test**: 댓글 작성/수정/삭제 동작, '수정됨' 표시, 관리자 타인 댓글 삭제 확인.

### Implementation for User Story 5

- [x] T049 [US5] Implement GET /articles/{id}/comments and POST /articles/{id}/comments endpoints in spec-kit/app/api/comments.py
- [x] T050 [US5] Implement POST /comments/{id}/edit with ownership check and is_edited flag in spec-kit/app/api/comments.py
- [x] T051 [US5] Implement POST /comments/{id}/delete with ownership or admin check in spec-kit/app/api/comments.py
- [x] T052 [US5] Create partials/_comments.html template with comment list, write form, edit/delete buttons (HTMX) in spec-kit/app/templates/partials/_comments.html
- [x] T053 [US5] Add comment section to article.html loading via HTMX in spec-kit/app/templates/article.html

**Checkpoint**: US5 fully functional - full comment CRUD with role-based deletion

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final touches across all user stories

- [x] T054 Verify soft-deleted articles excluded from all public queries (feed, search, scraps) in spec-kit/app/api/articles.py and spec-kit/app/api/scraps.py
- [x] T055 Add empty/loading states to HTMX interactions across all templates in spec-kit/app/templates/
- [x] T056 Create Python venv and verify app starts with uvicorn successfully
- [x] T057 Run seed_admin.py and verify admin login works end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1
- **US1 (Phase 3)**: Depends on Phase 2 - core article + crawler
- **US2 (Phase 4)**: Depends on Phase 2 - admin management (can parallel with US1)
- **US6 (Phase 5)**: Depends on Phase 3 (needs feed/article templates to gate)
- **US3 (Phase 6)**: Depends on Phase 2
- **US4 (Phase 7)**: Depends on Phase 2
- **US5 (Phase 8)**: Depends on Phase 3 (needs article detail page)
- **Polish (Phase 9)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: After Foundational - No dependencies on other stories
- **US2 (P1)**: After Foundational - Independent
- **US6 (P1)**: After US1 (needs templates)
- **US3 (P2)**: After Foundational - Independent
- **US4 (P2)**: After Foundational - Independent
- **US5 (P3)**: After US1 (needs article detail page)

### Parallel Opportunities

- **Phase 1**: T001-T005 sequential (project init)
- **Phase 2**: T008/T009/T016/T017 parallelizable
- **Phase 3**: T018/T019/T020 parallelizable (crawler modules)
- **Phase 4**: T037/T038/T039/T040 parallelizable (admin templates)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup → project skeleton
2. Phase 2: Foundational → DB, auth, templates config
3. Phase 3: US1 → article browsing with crawler
4. **STOP and VALIDATE**: verify feed, search, detail page work

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. US1 → Article browsing MVP
3. US2 → Admin management
4. US6 → Auth UI gating
5. US3 + US4 → Scrap + Like
6. US5 → Comments
7. Phase 9 → Polish

---

## Notes

- All file paths are relative to `spec-kit/`
- `claude/` directory must NOT be modified
- Auth is built from scratch (no reuse of existing claude/auth)
- Scrap uses dedicated `scraps` table (not UserNote)
- 57 total tasks
