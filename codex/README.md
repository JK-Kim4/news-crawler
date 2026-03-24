# AI Insights Service

`codex/` contains a production-oriented MVP for the AI insight collection service described in [`plan.md`](../plan.md).

## Stack

- Backend: FastAPI + SQLAlchemy + Celery
- Database: PostgreSQL
- Queue: Redis
- Frontend: Next.js App Router + TypeScript
- Infra: Docker Compose

## Features

- JSON-driven source bootstrap with Korean-first sample sources
- JWT auth with admin/user roles
- Feed, detail, search, bookmark, comment, and notification preference APIs
- Admin overview, source management, and manual crawl trigger API
- Celery-based scheduled/manual crawl pipeline with pluggable summarizer
- User-facing and admin-facing web pages

## Local Development

### Backend

```bash
cd backend
uv sync
uv run pytest -q
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd web
npm install
npm test
npm run dev
```

### Full Stack

```bash
docker compose up --build
```

## Service Layout

- `backend/`: API, data models, crawler, summarizer, worker
- `web/`: Next.js UI for feed, detail, auth, bookmarks, settings, admin
- `sources.json`: bootstrap source registry
- `docs/architecture.md`: architecture notes and roadmap alignment

