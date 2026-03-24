# Architecture Overview

## Purpose

The service ingests AI-related content from configurable feeds, summarizes it, stores the result, and exposes both a user-facing feed and an admin control surface.

## Major Components

- `sources.json`: bootstraps initial source definitions without code changes
- `backend/app/services/source_config.py`: loads and syncs source metadata into the database
- `backend/app/services/crawler.py`: consumes active sources, extracts feed/article payloads, persists normalized content
- `backend/app/services/summarizer.py`: summarizer abstraction with mock and OpenAI-backed modes
- `backend/app/api/`: public, user, and admin APIs
- `backend/app/tasks/crawl.py`: Celery task entrypoints for manual and scheduled crawl runs
- `web/app/`: Next.js pages for feed, detail, auth, bookmarks, settings, and admin

## Design Choices

- FastAPI provides a small, typed API surface that is easy to test.
- SQLAlchemy keeps persistence explicit and portable across SQLite tests and PostgreSQL deployment.
- Celery + Redis supports both scheduled crawl execution and manual admin triggers.
- Next.js App Router provides a clean split between server-rendered page composition and client interactions.
- The initial summarizer defaults to `mock` mode so the system remains runnable without external LLM credentials.

## Coverage Against `plan.md`

- Phase 1: source config, crawler structure, scheduler trigger, storage layer
- Phase 2: JWT auth, role guards, admin control API
- Phase 3: summarization abstraction, content API, bookmark/comment API
- Phase 4: user/admin web pages and notification settings UI
- Phase 5: notification preference storage and infrastructure scaffolding

