# AI Insights Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack AI news insights web service that ingests configurable sources, summarizes articles, exposes authenticated/admin APIs, and ships a user/admin web UI.

**Architecture:** Use a monorepo under `codex/` with a FastAPI backend, Celery worker/beat processes, PostgreSQL + Redis infrastructure, and a Next.js App Router frontend. Keep crawling, summarization, auth, and content interaction logic in separate backend modules so the service can start as an MVP and extend toward the full roadmap in `plan.md`.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, Alembic, Celery, Redis, PostgreSQL, Pydantic Settings, PyJWT/passlib, feedparser/BeautifulSoup/httpx, Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn-style component primitives, Docker Compose

---

### Task 1: Repository Structure And Shared Configuration

**Files:**
- Create: `codex/README.md`
- Create: `codex/.gitignore`
- Create: `codex/docker-compose.yml`
- Create: `codex/.env.example`
- Create: `codex/sources.json`
- Create: `codex/docs/architecture.md`

- [ ] **Step 1: Write the failing test**

Create a repository smoke test plan in `codex/README.md` that defines the expected services and commands.

- [ ] **Step 2: Run test to verify it fails**

Run: `test -f codex/docker-compose.yml`
Expected: FAIL because the project scaffold does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create the monorepo root with Docker services for `api`, `worker`, `beat`, `db`, `redis`, and `web`, plus environment variables and starter sources.

- [ ] **Step 4: Run test to verify it passes**

Run: `test -f codex/docker-compose.yml && test -f codex/sources.json`
Expected: PASS

### Task 2: Backend App Skeleton, Settings, And Database Models

**Files:**
- Create: `codex/backend/pyproject.toml`
- Create: `codex/backend/alembic.ini`
- Create: `codex/backend/app/__init__.py`
- Create: `codex/backend/app/main.py`
- Create: `codex/backend/app/core/config.py`
- Create: `codex/backend/app/core/security.py`
- Create: `codex/backend/app/db/base.py`
- Create: `codex/backend/app/db/session.py`
- Create: `codex/backend/app/models/*.py`
- Create: `codex/backend/app/schemas/*.py`
- Create: `codex/backend/app/api/*.py`
- Create: `codex/backend/app/services/*.py`
- Create: `codex/backend/alembic/versions/20260324_0001_initial_schema.py`
- Test: `codex/backend/tests/test_health.py`
- Test: `codex/backend/tests/test_source_config.py`

- [ ] **Step 1: Write the failing tests**

Write tests for:

```python
def test_healthcheck_returns_ok(): ...

def test_source_config_loads_active_sources(): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd codex/backend && pytest tests/test_health.py tests/test_source_config.py -q`
Expected: FAIL because the FastAPI app and source loader are missing.

- [ ] **Step 3: Write minimal implementation**

Create the FastAPI entrypoint, settings, SQLAlchemy models for `User`, `Content`, `Bookmark`, `Comment`, `Source`, `CrawlJob`, and `NotificationPreference`, plus the source config loader.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd codex/backend && pytest tests/test_health.py tests/test_source_config.py -q`
Expected: PASS

### Task 3: Auth, Content, Interaction, And Admin APIs

**Files:**
- Modify: `codex/backend/app/api/*.py`
- Create: `codex/backend/app/api/deps.py`
- Create: `codex/backend/app/services/auth.py`
- Create: `codex/backend/app/services/content.py`
- Create: `codex/backend/app/services/crawler.py`
- Create: `codex/backend/app/services/summarizer.py`
- Test: `codex/backend/tests/test_auth_api.py`
- Test: `codex/backend/tests/test_content_api.py`
- Test: `codex/backend/tests/test_admin_api.py`

- [ ] **Step 1: Write the failing tests**

Write API tests that cover:

```python
def test_register_and_login_issue_tokens(): ...
def test_content_feed_filters_and_searches(): ...
def test_admin_can_trigger_crawl_job(): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd codex/backend && pytest tests/test_auth_api.py tests/test_content_api.py tests/test_admin_api.py -q`
Expected: FAIL because the routers and services are not wired.

- [ ] **Step 3: Write minimal implementation**

Implement JWT auth, role guards, feed/detail/search endpoints, bookmark/comment endpoints, source listing/update endpoints, and an admin crawl trigger endpoint that enqueues a Celery task.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd codex/backend && pytest tests/test_auth_api.py tests/test_content_api.py tests/test_admin_api.py -q`
Expected: PASS

### Task 4: Crawl And Summarization Pipeline

**Files:**
- Modify: `codex/backend/app/services/crawler.py`
- Modify: `codex/backend/app/services/summarizer.py`
- Create: `codex/backend/app/tasks/crawl.py`
- Create: `codex/backend/app/worker.py`
- Test: `codex/backend/tests/test_crawl_pipeline.py`

- [ ] **Step 1: Write the failing tests**

Write a pipeline test that proves a configured feed item becomes stored content with a generated summary.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd codex/backend && pytest tests/test_crawl_pipeline.py -q`
Expected: FAIL because the crawler and summarizer pipeline do not exist.

- [ ] **Step 3: Write minimal implementation**

Implement source-driven feed ingestion, article extraction helpers, a summarizer interface with mock/OpenAI modes, and Celery tasks for scheduled/manual crawl execution.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd codex/backend && pytest tests/test_crawl_pipeline.py -q`
Expected: PASS

### Task 5: Next.js User And Admin Web UI

**Files:**
- Create: `codex/web/package.json`
- Create: `codex/web/next.config.ts`
- Create: `codex/web/tsconfig.json`
- Create: `codex/web/app/**/*.tsx`
- Create: `codex/web/components/**/*.tsx`
- Create: `codex/web/lib/api.ts`
- Create: `codex/web/lib/types.ts`
- Create: `codex/web/tests/*.test.tsx`

- [ ] **Step 1: Write the failing tests**

Write UI tests for feed rendering, content detail rendering, and admin dashboard actions.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd codex/web && npm test -- --runInBand`
Expected: FAIL because the frontend app has not been created.

- [ ] **Step 3: Write minimal implementation**

Create App Router pages for home feed, article detail, bookmarks, login/register, notification settings, and `/admin` monitoring/trigger pages. Add a typed API client and reusable UI components.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd codex/web && npm test -- --runInBand`
Expected: PASS

### Task 6: Documentation And End-To-End Verification

**Files:**
- Modify: `codex/README.md`
- Modify: `codex/docs/architecture.md`
- Test: `codex/backend/tests/`
- Test: `codex/web/tests/`

- [ ] **Step 1: Write the failing checklist**

Document the expected end-to-end flows: register, crawl trigger, feed load, bookmark, comment, and admin monitoring.

- [ ] **Step 2: Run verification commands**

Run:

```bash
cd codex/backend && pytest -q
cd codex/web && npm test -- --runInBand
```

Expected: all relevant tests pass.

- [ ] **Step 3: Finalize docs**

Update the README with setup commands, architecture summary, and feature coverage versus `plan.md`.
