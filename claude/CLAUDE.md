# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language

사용자에게 답변할 때 한글로 응답한다. 코드와 커밋 메시지는 영어로 작성한다.

## Commands

```bash
# Install (editable mode)
pip install -e .

# Run dev server
uvicorn main:app --reload --port 8000

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_pipeline.py -v

# Run a single test
python -m pytest tests/test_pipeline.py::test_function_name -v
```

No linter or formatter is configured.

## Architecture

AI news crawler that fetches articles from 31 tech blog sources (RSS + scraper), scores them, and serves a web UI.

### Data Flow

`config/sources.json` → `crawler/loader.py` syncs to DB → `crawler/runner.py` orchestrates crawls (APScheduler, 6h interval) → `crawler/sources/rss.py` or `scraper.py` fetches items → `crawler/pipeline.py` deduplicates, extracts keywords, scores (0-100), saves to SQLite + FTS5 index.

### Scoring: `crawler/pipeline.py`

`total = source_weight×5 (0-50) + recency (5-30) + keyword_count×2 (0-20)` capped at 100. Keywords defined in `crawler/keywords.py` (25 AI terms).

### Web Layer

FastAPI app in `main.py` with two routers: `api/articles.py` (feed, bookmarks, search, detail, bookmark/memo/tags/translate, manual crawl) and `api/sources.py` (source management, toggle). Templates in `ui/templates/` use Jinja2 + HTMX + Tailwind CSS (Play CDN).

### Database: SQLite + SQLAlchemy 2.0

Four tables in `db/models.py`: `sources`, `articles`, `user_notes`, `crawl_failures`. Plus `article_fts` FTS5 virtual table with trigram tokenizer for Korean+English search. Session management in `db/session.py`.

### Crawler Types

- `RssCrawler` (`crawler/sources/rss.py`): feedparser-based RSS/Atom
- `ScraperCrawler` (`crawler/sources/scraper.py`): BeautifulSoup4 HTML parsing

Both extend `BaseCrawler` in `crawler/sources/base.py` and return `CrawledItem` dataclass instances.

### Key Patterns

- Lifespan handler in `main.py` runs `init_db()`, `load_and_sync_sources()`, `start_scheduler()` on startup
- HTMX partial responses: many endpoints return HTML fragments, not full pages
- `api/helpers.py` provides shared utilities (JSON parsing, tag parsing, article enrichment, sidebar context)
- `api/templates.py` configures Jinja2 with custom filters (`relative_time`, `score_badge_class`)
- Translation uses `deep-translator` GoogleTranslator (free, no API key)
- Crawl failures tracked with retry logic (max 3 retries) in `crawler/runner.py`
