# AI 아카이브 고도화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 단순 뉴스 피드를 북마크·메모·태그·검색이 가능한 개인 AI 기술 아카이브로 고도화하고, 한국/해외 소스를 대폭 확충한다.

**Architecture:** 기존 FastAPI + SQLAlchemy 2.0 + SQLite + Jinja2 + HTMX 스택 유지. `UserNote` 테이블 신규 추가, SQLite FTS5 가상 테이블로 전문 검색 구현, `deep-translator`로 온디맨드 번역. UI는 Pico CSS → Tailwind CSS Play CDN으로 전면 교체하고 사이드바 레이아웃으로 전환.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, SQLite FTS5 (trigram), Jinja2, HTMX, Tailwind CSS Play CDN, deep-translator

**Spec:** `docs/superpowers/specs/2026-03-19-archive-upgrade-design.md`

---

## 파일 구조

| 파일 | 작업 | 역할 |
|------|------|------|
| `pyproject.toml` | 수정 | deep-translator 의존성 추가 |
| `db/models.py` | 수정 | Source.country, UserNote 클래스 추가 |
| `db/session.py` | 수정 | init_db()에 ALTER TABLE, FTS DDL, rebuild 추가 |
| `tests/conftest.py` | 수정 | FTS DDL을 fixture에 추가 |
| `tests/test_models.py` | 수정 | UserNote 테스트, Source.country 기본값 테스트 |
| `config/sources.json` | 수정 | country 필드 추가, 신규 소스 17개 추가 |
| `crawler/loader.py` | 수정 | country optional 필드 처리 |
| `tests/test_loader.py` | 수정 | country 관련 테스트 추가 |
| `crawler/pipeline.py` | 수정 | Article 저장 후 FTS INSERT 추가 |
| `tests/test_pipeline.py` | 수정 | FTS 동기화 테스트 추가 |
| `api/articles.py` | 수정 | bookmark/memo/tags/translate/bookmarks/search 엔드포인트 추가 |
| `ui/templates/base.html` | 수정 | Tailwind CDN, 사이드바 레이아웃 |
| `ui/templates/feed.html` | 수정 | country 탭, 카드 Tailwind 재작성 |
| `ui/templates/article.html` | 수정 | UserNote 표시, 번역 버튼 |
| `ui/templates/sources.html` | 수정 | country 컬럼 추가 |
| `ui/templates/bookmarks.html` | 신규 | 북마크 목록 페이지 |
| `ui/templates/search.html` | 신규 | 검색 결과 페이지 |

---

## Task 1: 의존성 추가

**Files:**
- Modify: `ai-news-crawler/pyproject.toml`

- [ ] **Step 1: deep-translator 의존성 추가**

`pyproject.toml`의 `dependencies` 목록에 추가:

```toml
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "apscheduler>=3.10",
    "httpx>=0.27",
    "feedparser>=6.0",
    "beautifulsoup4>=4.12",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",
    "deep-translator>=1.11.0",
]
```

- [ ] **Step 2: 패키지 설치 확인**

```bash
cd ai-news-crawler && pip install -e .
python -c "from deep_translator import GoogleTranslator; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: 커밋**

```bash
git add ai-news-crawler/pyproject.toml
git commit -m "chore: deep-translator 의존성 추가"
```

---

## Task 2: DB 모델 확장

**Files:**
- Modify: `ai-news-crawler/db/models.py`
- Modify: `ai-news-crawler/tests/test_models.py`

- [ ] **Step 1: 실패 테스트 작성 — Source.country 기본값**

`tests/test_models.py`에 추가:

```python
def test_source_country_default(db):
    source = Source(name="Test Blog", url="https://test-country.com/feed", type="rss", weight=7)
    db.add(source)
    db.commit()
    assert source.country == "global"


def test_source_country_kr(db):
    source = Source(name="KR Blog", url="https://kr-blog.com/feed", type="rss", weight=7, country="kr")
    db.add(source)
    db.commit()
    assert source.country == "kr"
```

- [ ] **Step 2: 실패 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_models.py::test_source_country_default -v
```

Expected: FAIL (AttributeError: Source has no attribute country)

- [ ] **Step 3: Source에 country 필드 추가**

`db/models.py`의 Source 클래스에 추가 (`weight` 컬럼 다음):

```python
country = Column(String(10), default="global", nullable=False)  # "kr" | "global"
```

- [ ] **Step 4: 실패 테스트 작성 — UserNote**

`tests/test_models.py`에 추가:

```python
def test_user_note_creation(db):
    source = Source(name="Test", url="https://note-test.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(url="https://note-test.com/a/1", title="Test", source_id=source.id,
                      score=50, score_breakdown="{}", tags="[]")
    db.add(article)
    db.commit()

    note = UserNote(article_id=article.id)
    db.add(note)
    db.commit()
    assert note.is_bookmarked is False
    assert note.memo is None
    assert note.user_tags == "[]"
    assert note.created_at is not None


def test_user_note_unique_per_article(db):
    source = Source(name="Test2", url="https://note-test2.com/feed", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(url="https://note-test2.com/a/1", title="Test", source_id=source.id,
                      score=50, score_breakdown="{}", tags="[]")
    db.add(article)
    db.commit()

    note1 = UserNote(article_id=article.id, is_bookmarked=True)
    note2 = UserNote(article_id=article.id)
    db.add(note1)
    db.commit()
    db.add(note2)
    with pytest.raises(IntegrityError):
        db.commit()
```

- [ ] **Step 5: UserNote 클래스 추가**

`db/models.py` 상단 import에 `Boolean, Text` 이미 있음을 확인. `Article` 클래스 아래에 추가:

```python
class UserNote(Base):
    __tablename__ = "user_notes"

    id            = Column(Integer, primary_key=True)
    article_id    = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    memo          = Column(Text, nullable=True)
    user_tags     = Column(Text, default="[]", nullable=False)  # JSON array string
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    article = relationship("Article", backref="user_note", uselist=False)
```

- [ ] **Step 6: 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_models.py -v
```

Expected: 전체 PASS (기존 3개 + 신규 4개)

- [ ] **Step 7: 커밋**

```bash
git add ai-news-crawler/db/models.py ai-news-crawler/tests/test_models.py
git commit -m "feat: Source.country, UserNote 모델 추가"
```

---

## Task 3: init_db() 마이그레이션 + conftest 업데이트

**Files:**
- Modify: `ai-news-crawler/db/session.py`
- Modify: `ai-news-crawler/tests/conftest.py`

- [ ] **Step 1: session.py의 init_db() 업데이트**

`db/session.py`를 다음으로 교체:

```python
import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base

logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_news.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def init_db():
    Base.metadata.create_all(engine)

    with engine.connect() as conn:
        # sources 테이블에 country 컬럼 추가 (기존 DB 마이그레이션)
        try:
            conn.execute(text("ALTER TABLE sources ADD COLUMN country TEXT DEFAULT 'global'"))
            conn.commit()
        except Exception:
            pass  # 컬럼이 이미 존재하면 무시

        # FTS5 가상 테이블 생성 (trigram tokenizer로 한국어 포함 검색 지원)
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS article_fts
            USING fts5(
                title, content,
                content='articles',
                content_rowid='id',
                tokenize='trigram'
            )
        """))
        conn.commit()

        # 기존 데이터 FTS 인덱싱 (rebuild은 멱등적으로 동작)
        try:
            conn.execute(text("INSERT INTO article_fts(article_fts) VALUES('rebuild')"))
            conn.commit()
        except Exception as e:
            logger.warning("FTS rebuild failed: %s", e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: conftest.py에 FTS DDL 추가**

`tests/conftest.py`를 다음으로 교체 (FTS를 필요로 하는 테스트를 위해 `db_fts` 픽스처 추가):

```python
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Base


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_fts():
    """FTS5 가상 테이블이 포함된 인메모리 DB 픽스처."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS article_fts
            USING fts5(
                title, content,
                content='articles',
                content_rowid='id',
                tokenize='trigram'
            )
        """))
        conn.commit()
    Session = sessionmaker(engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()
```

- [ ] **Step 3: 기존 테스트 전체 통과 확인**

```bash
cd ai-news-crawler && python -m pytest tests/ -v
```

Expected: 전체 PASS

- [ ] **Step 4: 커밋**

```bash
git add ai-news-crawler/db/session.py ai-news-crawler/tests/conftest.py
git commit -m "feat: init_db() ALTER TABLE, FTS5 마이그레이션 추가"
```

---

## Task 4: sources.json 업데이트 + loader.py country 처리

**Files:**
- Modify: `ai-news-crawler/config/sources.json`
- Modify: `ai-news-crawler/crawler/loader.py`
- Modify: `ai-news-crawler/tests/test_loader.py`

- [ ] **Step 1: 실패 테스트 작성 — country optional 처리**

`tests/test_loader.py`에 추가:

```python
def test_country_optional_defaults_to_global(tmp_path, db):
    """country 필드가 없으면 global 기본값으로 처리된다."""
    config = tmp_path / "sources.json"
    config.write_text('{"sources": [{"name": "No Country", "url": "https://nocountry.com/feed", "type": "rss", "weight": 5}]}')
    load_and_sync_sources(db, str(config))
    source = db.query(Source).filter_by(url="https://nocountry.com/feed").first()
    assert source.country == "global"


def test_country_kr_synced(tmp_path, db):
    """country 필드가 kr이면 DB에 반영된다."""
    config = tmp_path / "sources.json"
    config.write_text('{"sources": [{"name": "KR", "url": "https://kr-test.com/feed", "type": "rss", "weight": 5, "country": "kr"}]}')
    load_and_sync_sources(db, str(config))
    source = db.query(Source).filter_by(url="https://kr-test.com/feed").first()
    assert source.country == "kr"
```

- [ ] **Step 2: 실패 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_loader.py::test_country_optional_defaults_to_global -v
```

Expected: FAIL

- [ ] **Step 3: loader.py에 country 처리 추가**

`crawler/loader.py`의 Source 생성/업데이트 부분을 수정:

```python
for entry in entries:
    url = entry["url"]
    country = entry.get("country", "global")  # optional, 기본값 global
    if url in existing:
        src = existing[url]
        src.name = entry["name"]
        src.type = entry["type"]
        src.weight = entry["weight"]
        src.country = country
    else:
        db.add(Source(
            name=entry["name"],
            url=url,
            type=entry["type"],
            weight=entry["weight"],
            country=country,
        ))
```

- [ ] **Step 4: 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_loader.py -v
```

Expected: 전체 PASS

- [ ] **Step 5: sources.json 전면 업데이트**

`config/sources.json`을 다음으로 교체 (기존 소스에 country 추가 + 신규 소스 17개 추가):

```json
{
  "sources": [
    { "name": "ArXiv AI",              "url": "https://arxiv.org/rss/cs.AI",                                          "type": "rss",     "weight": 10, "country": "global" },
    { "name": "ArXiv ML",              "url": "https://arxiv.org/rss/cs.LG",                                          "type": "rss",     "weight": 10, "country": "global" },
    { "name": "OpenAI Blog",           "url": "https://openai.com/blog",                                              "type": "scraper", "weight": 9,  "country": "global" },
    { "name": "Anthropic Blog",        "url": "https://www.anthropic.com/news",                                       "type": "scraper", "weight": 9,  "country": "global" },
    { "name": "Google AI Blog",        "url": "https://ai.googleblog.com/feeds/posts/default",                        "type": "rss",     "weight": 9,  "country": "global" },
    { "name": "Google DeepMind",       "url": "https://deepmind.com/blog/feed/basic/",                                "type": "rss",     "weight": 9,  "country": "global" },
    { "name": "HuggingFace Blog",      "url": "https://huggingface.co/blog/feed.xml",                                 "type": "rss",     "weight": 8,  "country": "global" },
    { "name": "Microsoft Research",    "url": "https://www.microsoft.com/en-us/research/feed/",                       "type": "rss",     "weight": 8,  "country": "global" },
    { "name": "NVIDIA Developer AI",   "url": "https://developer.nvidia.com/blog/feed",                               "type": "rss",     "weight": 8,  "country": "global" },
    { "name": "Meta AI Blog",          "url": "https://ai.meta.com/blog/",                                            "type": "scraper", "weight": 8,  "country": "global" },
    { "name": "Netflix Tech Blog",     "url": "https://netflixtechblog.com/feed",                                     "type": "rss",     "weight": 7,  "country": "global" },
    { "name": "ByteByteGo",            "url": "https://blog.bytebytego.com/feed",                                     "type": "rss",     "weight": 7,  "country": "global" },
    { "name": "Uber Engineering AI",   "url": "https://eng.uber.com/category/articles/ai/feed",                       "type": "rss",     "weight": 7,  "country": "global" },
    { "name": "IEEE Spectrum AI",      "url": "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",    "type": "rss",     "weight": 7,  "country": "global" },
    { "name": "Interconnects",         "url": "https://www.interconnects.ai/feed",                                    "type": "rss",     "weight": 7,  "country": "global" },
    { "name": "Hacker News AI",        "url": "https://hnrss.org/newest?q=AI&points=50",                              "type": "rss",     "weight": 6,  "country": "global" },
    { "name": "Naver D2",              "url": "https://d2.naver.com/rss/d2.xml",                                      "type": "rss",     "weight": 8,  "country": "kr" },
    { "name": "Kakao Tech Blog",       "url": "https://kakaotech.io/feed",                                            "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Toss Tech Blog",        "url": "https://toss.tech/rss.xml",                                            "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Woowa Tech Blog",       "url": "https://techblog.woowahan.com/feed",                                   "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Socar Tech Blog",       "url": "https://tech.socarcorp.kr/feed",                                       "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Kurly Tech Blog",       "url": "https://helloworld.kurly.com/feed.xml",                                "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Banksalad Tech Blog",   "url": "https://blog.banksalad.com/rss.xml",                                   "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "KakaoPay Tech Blog",    "url": "https://tech.kakaopay.com/rss.xml",                                    "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Kakao Enterprise",      "url": "https://tech.kakaoenterprise.com/feed",                                "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Line Tech Blog",        "url": "https://techblog.lycorp.co.jp/ko/feed/index",                          "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Daangn Tech Blog",      "url": "https://medium.com/feed/daangn",                                       "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Coupang Engineering",   "url": "https://medium.com/feed/coupang-engineering",                          "type": "rss",     "weight": 7,  "country": "kr" },
    { "name": "Devsisters Tech Blog",  "url": "https://tech.devsisters.com/rss.xml",                                  "type": "rss",     "weight": 6,  "country": "kr" },
    { "name": "Musinsa Tech Blog",     "url": "https://medium.com/feed/musinsa-tech",                                 "type": "rss",     "weight": 6,  "country": "kr" },
    { "name": "Hyperconnect Tech",     "url": "https://hyperconnect.github.io/feed.xml",                              "type": "rss",     "weight": 6,  "country": "kr" }
  ]
}
```

- [ ] **Step 6: 전체 테스트 통과 확인**

```bash
cd ai-news-crawler && python -m pytest tests/ -v
```

Expected: 전체 PASS

- [ ] **Step 7: 커밋**

```bash
git add ai-news-crawler/config/sources.json ai-news-crawler/crawler/loader.py ai-news-crawler/tests/test_loader.py
git commit -m "feat: sources.json country 필드 추가, 소스 31개로 확충"
```

---

## Task 5: pipeline.py FTS 동기화

**Files:**
- Modify: `ai-news-crawler/crawler/pipeline.py`
- Modify: `ai-news-crawler/tests/test_pipeline.py`

- [ ] **Step 1: 실패 테스트 작성 — FTS INSERT 확인**

`tests/test_pipeline.py`에 추가 (db_fts 픽스처 사용):

```python
from sqlalchemy import text

def test_process_item_syncs_fts(db_fts):
    """process_item 후 article_fts에 인덱싱된다."""
    source = Source(name="FTS Test", url="https://fts-test.com/feed", type="rss", weight=8)
    db_fts.add(source)
    db_fts.commit()

    item = CrawledItem(
        url="https://fts-test.com/a/1",
        title="Large language model fine-tuning guide",
        content="This article covers fine-tuning LLM with LoRA technique.",
        published_at=None,
    )
    article = process_item(db_fts, source, item)
    assert article is not None

    rows = db_fts.execute(
        text("SELECT rowid FROM article_fts WHERE article_fts MATCH 'fine-tuning'")
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == article.id
```

- [ ] **Step 2: 실패 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_pipeline.py::test_process_item_syncs_fts -v
```

Expected: FAIL

- [ ] **Step 3: pipeline.py에 FTS INSERT 추가**

`crawler/pipeline.py`의 import에 `text` 추가:

```python
from sqlalchemy import text
```

`process_item()`의 `db.refresh(article)` 다음에 추가:

```python
        db.refresh(article)
        # FTS 인덱스 동기화 (실패해도 article 저장은 유지)
        try:
            db.execute(
                text("INSERT INTO article_fts(rowid, title, content) VALUES (:id, :title, :content)"),
                {"id": article.id, "title": article.title, "content": article.content or ""},
            )
            db.commit()
        except Exception as e:
            logger.warning("FTS insert failed for article %s: %s", article.id, e)
        return article
```

- [ ] **Step 4: 테스트 실행 확인**

```bash
cd ai-news-crawler && python -m pytest tests/test_pipeline.py -v
```

Expected: 전체 PASS (기존 4개 + 신규 1개)

- [ ] **Step 5: 커밋**

```bash
git add ai-news-crawler/crawler/pipeline.py ai-news-crawler/tests/test_pipeline.py
git commit -m "feat: pipeline에 FTS5 인덱스 동기화 추가"
```

---

## Task 6: UserNote API 엔드포인트 (북마크·메모·태그)

**Files:**
- Modify: `ai-news-crawler/api/articles.py`

- [ ] **Step 1: UserNote 헬퍼 함수 작성**

`api/articles.py` 상단 import에 추가:

```python
import json
from db.models import Article, Source, UserNote
```

파일 내부에 헬퍼 추가 (기존 라우터 정의 위):

```python
def _get_or_create_note(db: Session, article_id: int) -> UserNote:
    """article_id에 해당하는 UserNote를 가져오거나 생성한다."""
    note = db.query(UserNote).filter_by(article_id=article_id).first()
    if not note:
        note = UserNote(article_id=article_id)
        db.add(note)
        db.commit()
        db.refresh(note)
    return note
```

- [ ] **Step 2: 북마크 토글 엔드포인트 추가**

`api/articles.py`에 추가:

```python
@router.post("/articles/{article_id}/bookmark")
def toggle_bookmark(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = _get_or_create_note(db, article_id)
    note.is_bookmarked = not note.is_bookmarked
    db.commit()
    icon = "🔖" if note.is_bookmarked else "☆"
    label = "북마크됨" if note.is_bookmarked else "북마크"
    return HTMLResponse(
        f'<button class="action-btn bookmark-btn" hx-post="/articles/{article_id}/bookmark" hx-swap="outerHTML">'
        f'{icon} {label}</button>'
    )
```

- [ ] **Step 3: 메모 저장 엔드포인트 추가**

```python
@router.post("/articles/{article_id}/memo")
async def save_memo(article_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    memo_text = form.get("memo", "").strip()
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = _get_or_create_note(db, article_id)
    note.memo = memo_text or None
    db.commit()
    preview = (memo_text[:50] + "...") if len(memo_text) > 50 else memo_text
    if preview:
        return HTMLResponse(
            f'<div class="memo-preview" id="memo-{article_id}">'
            f'📝 "{preview}" '
            f'<button hx-get="/articles/{article_id}/memo-form" hx-target="#memo-{article_id}" hx-swap="outerHTML">수정</button>'
            f'</div>'
        )
    return HTMLResponse(
        f'<div id="memo-{article_id}">'
        f'<button hx-get="/articles/{article_id}/memo-form" hx-target="#memo-{article_id}" hx-swap="outerHTML">📝 메모 추가</button>'
        f'</div>'
    )


@router.get("/articles/{article_id}/memo-form")
def memo_form(article_id: int, db: Session = Depends(get_db)):
    note = db.query(UserNote).filter_by(article_id=article_id).first()
    current = note.memo or "" if note else ""
    return HTMLResponse(
        f'<form id="memo-{article_id}" hx-post="/articles/{article_id}/memo" hx-target="#memo-{article_id}" hx-swap="outerHTML">'
        f'<textarea name="memo" rows="3" style="width:100%">{current}</textarea>'
        f'<button type="submit">저장</button>'
        f'<button type="button" onclick="this.closest(\'form\').outerHTML=\'\'">취소</button>'
        f'</form>'
    )
```

- [ ] **Step 4: 커스텀 태그 저장 엔드포인트 추가**

```python
@router.post("/articles/{article_id}/tags")
async def save_user_tags(article_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    raw = form.get("user_tags", "")
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = _get_or_create_note(db, article_id)
    note.user_tags = json.dumps(tags, ensure_ascii=False)
    db.commit()
    tags_html = "".join(f'<span class="tag custom-tag">{t}</span>' for t in tags)
    return HTMLResponse(
        f'<div class="custom-tags" id="user-tags-{article_id}">'
        f'{tags_html}'
        f'<button hx-get="/articles/{article_id}/tags-form" hx-target="#user-tags-{article_id}" hx-swap="outerHTML">+태그</button>'
        f'</div>'
    )


@router.get("/articles/{article_id}/tags-form")
def tags_form(article_id: int, db: Session = Depends(get_db)):
    note = db.query(UserNote).filter_by(article_id=article_id).first()
    current = ",".join(json.loads(note.user_tags)) if note and note.user_tags else ""
    return HTMLResponse(
        f'<form id="user-tags-{article_id}" hx-post="/articles/{article_id}/tags" hx-target="#user-tags-{article_id}" hx-swap="outerHTML" style="display:inline">'
        f'<input name="user_tags" value="{current}" placeholder="태그1,태그2" style="width:200px">'
        f'<button type="submit">저장</button>'
        f'</form>'
    )
```

- [ ] **Step 5: 북마크 목록 페이지 엔드포인트 추가**

```python
@router.get("/bookmarks", response_class=HTMLResponse)
def bookmarks_page(request: Request, db: Session = Depends(get_db)):
    notes = db.query(UserNote).filter_by(is_bookmarked=True).all()
    article_ids = [n.article_id for n in notes]
    articles = db.query(Article).filter(Article.id.in_(article_ids)).order_by(Article.score.desc()).all()

    note_map = {n.article_id: n for n in notes}
    for a in articles:
        a.tags_list = json.loads(a.tags or "[]")
        note = note_map.get(a.id)
        a.user_note = note

    return templates.TemplateResponse("bookmarks.html", {
        "request": request,
        "articles": articles,
    })
```

- [ ] **Step 6: 서버 재시작 후 엔드포인트 수동 확인**

```bash
cd ai-news-crawler && uvicorn main:app --reload --port 8000
```

브라우저에서 임의 아티클의 북마크 버튼 클릭 → HTMX 응답 확인

- [ ] **Step 7: 커밋**

```bash
git add ai-news-crawler/api/articles.py
git commit -m "feat: 북마크/메모/커스텀태그 API 엔드포인트 추가"
```

---

## Task 7: 검색 API (FTS5)

**Files:**
- Modify: `ai-news-crawler/api/articles.py`

- [ ] **Step 1: 검색 엔드포인트 추가**

`api/articles.py`에 import 추가:

```python
from sqlalchemy import text
```

검색 엔드포인트 추가:

```python
@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = "",
    country: str = "",
    db: Session = Depends(get_db),
):
    articles = []
    if q:
        try:
            rows = db.execute(
                text("SELECT rowid FROM article_fts WHERE article_fts MATCH :q ORDER BY rank LIMIT 50"),
                {"q": q},
            ).fetchall()
            article_ids = [r[0] for r in rows]

            query = db.query(Article).join(Source).filter(Article.id.in_(article_ids))
            if country in ("kr", "global"):
                query = query.filter(Source.country == country)
            articles = query.all()

            # FTS rank 순서 유지
            order_map = {aid: i for i, aid in enumerate(article_ids)}
            articles.sort(key=lambda a: order_map.get(a.id, 999))
        except Exception as e:
            logger.warning("FTS search failed: %s", e)

    for a in articles:
        a.tags_list = json.loads(a.tags or "[]")
        note = db.query(UserNote).filter_by(article_id=a.id).first()
        a.user_note = note

    return templates.TemplateResponse("search.html", {
        "request": request,
        "articles": articles,
        "q": q,
        "country": country,
    })
```

- [ ] **Step 2: 커밋**

```bash
git add ai-news-crawler/api/articles.py
git commit -m "feat: FTS5 기반 전문 검색 엔드포인트 추가"
```

---

## Task 8: 번역 API

**Files:**
- Modify: `ai-news-crawler/api/articles.py`

- [ ] **Step 1: 번역 엔드포인트 추가**

```python
@router.post("/articles/{article_id}/translate")
def translate_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).join(Source).filter(Article.id == article_id).first()
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    if article.source.country != "global":
        return JSONResponse({"error": "한국어 아티클은 번역이 필요하지 않습니다"}, status_code=400)

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="auto", target="ko")

        title_kr = translator.translate(article.title[:500])
        content_snippet = (article.content or "")[:500]
        content_kr = translator.translate(content_snippet) if content_snippet else ""

        html = (
            f'<div class="translation-result" id="translation-{article_id}">'
            f'<h4>한글 요약</h4>'
            f'<p><strong>{title_kr}</strong></p>'
            f'<p>{content_kr}</p>'
            f'<small>* 제목 + 본문 앞 500자 번역 (deep-translator)</small>'
            f'</div>'
        )
        return HTMLResponse(html)
    except Exception as e:
        logger.warning("Translation failed for article %s: %s", article_id, e)
        return HTMLResponse(
            f'<div id="translation-{article_id}" class="text-red-500">번역을 가져올 수 없습니다</div>'
        )
```

- [ ] **Step 2: 커밋**

```bash
git add ai-news-crawler/api/articles.py
git commit -m "feat: 온디맨드 번역 API 추가 (deep-translator, 해외 아티클 전용)"
```

---

## Task 9: UI 기반 재설계 — base.html (사이드바 레이아웃)

**Files:**
- Modify: `ai-news-crawler/ui/templates/base.html`

- [ ] **Step 1: base.html 전면 재작성**

`ui/templates/base.html`을 다음으로 교체:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Archive</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@1.9.12"></script>
</head>
<body class="bg-slate-100 text-slate-800 h-screen flex overflow-hidden">

  <!-- 사이드바 -->
  <aside class="w-56 bg-slate-900 text-slate-200 flex flex-col flex-shrink-0">
    <div class="px-4 py-5 border-b border-slate-700">
      <div class="font-bold text-white text-lg">AI Archive</div>
      <div class="text-slate-400 text-xs mt-0.5">AI 기술 아카이브</div>
    </div>

    <nav class="flex-1 py-2">
      <div class="px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-500 mt-2">메뉴</div>
      <a href="/" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'feed' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
        <span>📰</span> 피드
      </a>
      <a href="/bookmarks" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'bookmarks' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
        <span>🔖</span> 북마크
      </a>
      <a href="/search" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'search' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
        <span>🔍</span> 검색
      </a>
      <div class="px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-500 mt-4">관리</div>
      <a href="/sources" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'sources' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
        <span>📡</span> 소스 관리
      </a>
    </nav>

    <div class="px-4 py-4 border-t border-slate-700">
      <div class="text-xs text-slate-500 mb-2" id="crawl-status">크롤링 대기 중</div>
      <button
        class="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded"
        hx-post="/api/crawl"
        hx-target="#crawl-result"
        hx-indicator="#crawl-spinner"
        hx-disabled-elt="this"
        hx-on::after-request="document.getElementById('crawl-status').textContent='크롤링 완료'; setTimeout(()=>window.location.reload(),1000)">
        ⟳ 지금 크롤링
      </button>
      <span id="crawl-spinner" class="htmx-indicator text-xs text-slate-400 block mt-1">크롤링 중...</span>
      <div id="crawl-result"></div>
    </div>
  </aside>

  <!-- 메인 -->
  <main class="flex-1 flex flex-col overflow-hidden">
    {% block content %}{% endblock %}
  </main>

</body>
</html>
```

- [ ] **Step 2: 서버 기동 후 사이드바 레이아웃 시각 확인**

```bash
cd ai-news-crawler && uvicorn main:app --reload --port 8000
```

http://localhost:8000 접속 → 사이드바 표시 확인

- [ ] **Step 3: 커밋**

```bash
git add ai-news-crawler/ui/templates/base.html
git commit -m "feat: Tailwind CSS 사이드바 레이아웃으로 UI 기반 재설계"
```

---

## Task 10: 피드 페이지 재설계

**Files:**
- Modify: `ai-news-crawler/ui/templates/feed.html`
- Modify: `ai-news-crawler/api/articles.py` (feed 라우터에 UserNote 정보 추가)

- [ ] **Step 1: feed 라우터에 UserNote 데이터 추가**

`api/articles.py`의 `feed()` 함수에서 articles 조회 후 다음 추가:

```python
    note_map = {}
    if articles:
        notes = db.query(UserNote).filter(
            UserNote.article_id.in_([a.id for a in articles])
        ).all()
        note_map = {n.article_id: n for n in notes}

    for a in articles:
        a.tags_list = json.loads(a.tags or "[]")
        a.user_note = note_map.get(a.id)
```

- [ ] **Step 2: feed.html 전면 재작성**

`ui/templates/feed.html`을 다음으로 교체:

```html
{% extends "base.html" %}
{% set active_page = 'feed' %}
{% block content %}

<!-- 헤더 -->
<div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4 flex-shrink-0">
  <h1 class="text-lg font-bold text-slate-800">피드</h1>

  <!-- 국가 탭 -->
  <div class="flex gap-1">
    <a href="/?sort={{ sort }}&country=&{% if unread_only %}unread=true{% endif %}"
       class="px-3 py-1 rounded-full text-sm {% if not selected_country %}bg-slate-800 text-white{% else %}text-slate-500 border border-slate-200 hover:bg-slate-50{% endif %}">
      전체
    </a>
    <a href="/?sort={{ sort }}&country=kr&{% if unread_only %}unread=true{% endif %}"
       class="px-3 py-1 rounded-full text-sm {% if selected_country == 'kr' %}bg-slate-800 text-white{% else %}text-slate-500 border border-slate-200 hover:bg-slate-50{% endif %}">
      🇰🇷 한국
    </a>
    <a href="/?sort={{ sort }}&country=global&{% if unread_only %}unread=true{% endif %}"
       class="px-3 py-1 rounded-full text-sm {% if selected_country == 'global' %}bg-slate-800 text-white{% else %}text-slate-500 border border-slate-200 hover:bg-slate-50{% endif %}">
      🌏 해외
    </a>
  </div>

  <div class="ml-auto flex items-center gap-3">
    <a href="/search" class="text-sm text-slate-400 hover:text-slate-600">🔍 검색</a>
    <select name="sort" class="text-sm border border-slate-200 rounded px-2 py-1 text-slate-600"
            onchange="location.href='/?sort='+this.value+'&country={{ selected_country }}'">
      <option value="score" {% if sort == 'score' %}selected{% endif %}>스코어순</option>
      <option value="date" {% if sort == 'date' %}selected{% endif %}>최신순</option>
    </select>
    <label class="flex items-center gap-1 text-sm text-slate-500">
      <input type="checkbox" {% if unread_only %}checked{% endif %}
             onchange="location.href='/?sort={{ sort }}&country={{ selected_country }}&'+( this.checked?'unread=true':'')">
      안읽은 것만
    </label>
  </div>
</div>

<!-- 피드 -->
<div class="flex-1 overflow-y-auto p-6 flex flex-col gap-3">
  {% for article in articles %}
  {% set note = article.user_note %}
  <div class="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-sm hover:border-slate-300 transition {% if article.is_read %}opacity-55{% endif %}">

    <!-- 제목 + 스코어 -->
    <div class="flex justify-between items-start gap-3 mb-2">
      <a href="{{ article.url }}" target="_blank"
         class="font-semibold text-slate-800 hover:text-blue-600 leading-snug text-sm flex-1">
        {{ article.title }}
      </a>
      <span class="text-xs font-bold px-2 py-1 rounded-full flex-shrink-0 text-white
                   {% if article.score >= 90 %}bg-blue-600
                   {% elif article.score >= 70 %}bg-emerald-600
                   {% else %}bg-violet-600{% endif %}">
        {{ article.score }}점
      </span>
    </div>

    <!-- 메타 -->
    <div class="text-xs text-slate-500 mb-2 flex items-center gap-1.5">
      <span>{{ article.source.name }}</span>
      <span>·</span>
      <span>{{ '🇰🇷' if article.source.country == 'kr' else '🌏' }}</span>
      {% if article.published_at %}
      <span>· {{ article.published_at.strftime('%Y-%m-%d') }}</span>
      {% endif %}
      {% if article.is_read %}<span class="text-slate-400">· ✓ 읽음</span>{% endif %}
    </div>

    <!-- 태그 -->
    <div class="flex flex-wrap gap-1 mb-2">
      {% for tag in article.tags_list %}
      <span class="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
      {% endfor %}
      {% if note %}
      {% for tag in note.user_tags | from_json %}
      <span class="bg-yellow-50 text-yellow-700 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
      {% endfor %}
      {% endif %}
    </div>

    <!-- 메모 미리보기 -->
    {% if note and note.memo %}
    <div class="text-xs text-slate-600 bg-yellow-50 border-l-2 border-yellow-400 px-2 py-1 mb-2 rounded-r" id="memo-{{ article.id }}">
      📝 "{{ note.memo[:50] }}{% if note.memo|length > 50 %}...{% endif %}"
      <button class="ml-2 text-slate-400 hover:text-slate-600"
              hx-get="/articles/{{ article.id }}/memo-form"
              hx-target="#memo-{{ article.id }}"
              hx-swap="outerHTML">수정</button>
    </div>
    {% else %}
    <div id="memo-{{ article.id }}">
      <button class="text-xs text-slate-400 hover:text-slate-600"
              hx-get="/articles/{{ article.id }}/memo-form"
              hx-target="#memo-{{ article.id }}"
              hx-swap="outerHTML">📝 메모 추가</button>
    </div>
    {% endif %}

    <!-- 액션 버튼 -->
    <div class="flex items-center gap-2 mt-2">
      <button class="text-xs px-2 py-1 rounded border {% if note and note.is_bookmarked %}border-yellow-300 bg-yellow-50 text-yellow-700{% else %}border-slate-200 text-slate-500 hover:bg-slate-50{% endif %}"
              hx-post="/articles/{{ article.id }}/bookmark"
              hx-swap="outerHTML">
        {{ '🔖 북마크됨' if note and note.is_bookmarked else '☆ 북마크' }}
      </button>
      <div id="user-tags-{{ article.id }}" class="flex items-center gap-1">
        <button class="text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50"
                hx-get="/articles/{{ article.id }}/tags-form"
                hx-target="#user-tags-{{ article.id }}"
                hx-swap="outerHTML">+태그</button>
      </div>
      <button class="text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50"
              hx-post="/articles/{{ article.id }}/read"
              hx-swap="outerHTML">
        {{ '↩ 읽음취소' if article.is_read else '✓ 읽음' }}
      </button>
      <a href="{{ article.url }}" target="_blank"
         class="ml-auto text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50">
        원문 →
      </a>
    </div>
  </div>
  {% else %}
  <div class="text-center text-slate-400 py-20">
    <div class="text-4xl mb-4">📭</div>
    <p>수집된 아티클이 없습니다. 크롤링을 실행해보세요.</p>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 3: Jinja2 `from_json` 필터 등록**

`api/articles.py`의 `templates` 선언 아래에 추가:

```python
import json as _json
templates.env.filters["from_json"] = lambda s: _json.loads(s or "[]")
```

- [ ] **Step 4: feed 라우터에 `country` 필터 파라미터 추가**

`api/articles.py`의 `feed()` 함수 시그니처에 `country: str = ""` 추가:

```python
def feed(
    request: Request,
    sort: str = "score",
    source_id: int | None = None,
    tag: str | None = None,
    unread: bool = False,
    country: str = "",
    db: Session = Depends(get_db),
):
```

쿼리 필터 부분에 추가:

```python
    if country in ("kr", "global"):
        query = query.filter(Source.country == country)
```

`templates.TemplateResponse` 호출에 `selected_country` 추가:

```python
    return templates.TemplateResponse("feed.html", {
        ...
        "selected_country": country,
    })
```

- [ ] **Step 5: 브라우저에서 국가 탭 동작 확인**

http://localhost:8000 → 한국 탭 클릭 → 한국 소스만 표시되는지 확인

- [ ] **Step 6: 커밋**

```bash
git add ai-news-crawler/ui/templates/feed.html ai-news-crawler/api/articles.py
git commit -m "feat: 피드 페이지 Tailwind 재설계, 국가 탭 필터, UserNote 카드 표시"
```

---

## Task 11: 북마크·검색 페이지 신규 생성

**Files:**
- Create: `ai-news-crawler/ui/templates/bookmarks.html`
- Create: `ai-news-crawler/ui/templates/search.html`

- [ ] **Step 1: bookmarks.html 생성**

```html
{% extends "base.html" %}
{% set active_page = 'bookmarks' %}
{% block content %}
<div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4 flex-shrink-0">
  <h1 class="text-lg font-bold text-slate-800">🔖 북마크</h1>
  <span class="text-sm text-slate-400">{{ articles|length }}개</span>
</div>

<div class="flex-1 overflow-y-auto p-6 flex flex-col gap-3">
  {% for article in articles %}
  {% set note = article.user_note %}
  <div class="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-sm hover:border-slate-300 transition {% if article.is_read %}opacity-55{% endif %}">
    <div class="flex justify-between items-start gap-3 mb-2">
      <a href="{{ article.url }}" target="_blank"
         class="font-semibold text-slate-800 hover:text-blue-600 leading-snug text-sm flex-1">
        {{ article.title }}
      </a>
      <span class="text-xs font-bold px-2 py-1 rounded-full flex-shrink-0 text-white
                   {% if article.score >= 90 %}bg-blue-600{% elif article.score >= 70 %}bg-emerald-600{% else %}bg-violet-600{% endif %}">
        {{ article.score }}점
      </span>
    </div>
    <div class="text-xs text-slate-500 mb-2 flex items-center gap-1.5">
      <span>{{ article.source.name }}</span>
      <span>·</span>
      <span>{{ '🇰🇷' if article.source.country == 'kr' else '🌏' }}</span>
      {% if article.published_at %}<span>· {{ article.published_at.strftime('%Y-%m-%d') }}</span>{% endif %}
    </div>
    <div class="flex flex-wrap gap-1 mb-2">
      {% for tag in article.tags_list %}
      <span class="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
      {% endfor %}
      {% if note %}{% for tag in note.user_tags | from_json %}
      <span class="bg-yellow-50 text-yellow-700 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
      {% endfor %}{% endif %}
    </div>
    {% if note and note.memo %}
    <div class="text-xs text-slate-600 bg-yellow-50 border-l-2 border-yellow-400 px-2 py-1 mb-2 rounded-r">
      📝 "{{ note.memo[:80] }}{% if note.memo|length > 80 %}...{% endif %}"
    </div>
    {% endif %}
    <div class="flex items-center gap-2 mt-2">
      <button class="text-xs px-2 py-1 rounded border border-yellow-300 bg-yellow-50 text-yellow-700"
              hx-post="/articles/{{ article.id }}/bookmark"
              hx-swap="closest div.bg-white"
              hx-on::after-request="this.closest('.bg-white').remove()">
        🔖 북마크 해제
      </button>
      <a href="{{ article.url }}" target="_blank"
         class="ml-auto text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50">
        원문 →
      </a>
    </div>
  </div>
  {% else %}
  <div class="text-center text-slate-400 py-20">
    <div class="text-4xl mb-4">🔖</div>
    <p>북마크된 아티클이 없습니다.</p>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 2: search.html 생성**

```html
{% extends "base.html" %}
{% set active_page = 'search' %}
{% block content %}
<div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4 flex-shrink-0">
  <h1 class="text-lg font-bold text-slate-800">🔍 검색</h1>
  <form method="get" action="/search" class="flex items-center gap-2 flex-1">
    <input name="q" value="{{ q }}" placeholder="제목, 내용 검색..."
           class="flex-1 border border-slate-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-blue-400">
    <select name="country" class="text-sm border border-slate-200 rounded px-2 py-1.5 text-slate-600">
      <option value="" {% if not country %}selected{% endif %}>전체</option>
      <option value="kr" {% if country == 'kr' %}selected{% endif %}>🇰🇷 한국</option>
      <option value="global" {% if country == 'global' %}selected{% endif %}>🌏 해외</option>
    </select>
    <button type="submit" class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">검색</button>
  </form>
</div>

<div class="flex-1 overflow-y-auto p-6 flex flex-col gap-3">
  {% if q and not articles %}
  <div class="text-center text-slate-400 py-20">
    <div class="text-4xl mb-4">🔎</div>
    <p>"{{ q }}" 검색 결과가 없습니다.</p>
  </div>
  {% elif not q %}
  <div class="text-center text-slate-400 py-20">
    <div class="text-4xl mb-4">🔍</div>
    <p>검색어를 입력하세요.</p>
  </div>
  {% endif %}

  {% for article in articles %}
  {% set note = article.user_note %}
  <div class="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-sm hover:border-slate-300 transition {% if article.is_read %}opacity-55{% endif %}">
    <div class="flex justify-between items-start gap-3 mb-2">
      <a href="{{ article.url }}" target="_blank"
         class="font-semibold text-slate-800 hover:text-blue-600 leading-snug text-sm flex-1">
        {{ article.title }}
      </a>
      <span class="text-xs font-bold px-2 py-1 rounded-full flex-shrink-0 text-white
                   {% if article.score >= 90 %}bg-blue-600{% elif article.score >= 70 %}bg-emerald-600{% else %}bg-violet-600{% endif %}">
        {{ article.score }}점
      </span>
    </div>
    <div class="text-xs text-slate-500 mb-2 flex items-center gap-1.5">
      <span>{{ article.source.name }}</span>
      <span>·</span>
      <span>{{ '🇰🇷' if article.source.country == 'kr' else '🌏' }}</span>
      {% if article.published_at %}<span>· {{ article.published_at.strftime('%Y-%m-%d') }}</span>{% endif %}
    </div>
    <div class="flex flex-wrap gap-1 mb-2">
      {% for tag in article.tags_list %}
      <span class="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
      {% endfor %}
    </div>
    <div class="flex items-center gap-2 mt-2">
      <button class="text-xs px-2 py-1 rounded border {% if note and note.is_bookmarked %}border-yellow-300 bg-yellow-50 text-yellow-700{% else %}border-slate-200 text-slate-500 hover:bg-slate-50{% endif %}"
              hx-post="/articles/{{ article.id }}/bookmark"
              hx-swap="outerHTML">
        {{ '🔖 북마크됨' if note and note.is_bookmarked else '☆ 북마크' }}
      </button>
      <a href="{{ article.url }}" target="_blank"
         class="ml-auto text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50">
        원문 →
      </a>
    </div>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 3: 커밋**

```bash
git add ai-news-crawler/ui/templates/bookmarks.html ai-news-crawler/ui/templates/search.html
git commit -m "feat: 북마크·검색 페이지 신규 생성"
```

---

## Task 12: 아티클 상세·소스 관리 페이지 업데이트

**Files:**
- Modify: `ai-news-crawler/ui/templates/article.html`
- Modify: `ai-news-crawler/ui/templates/sources.html`
- Modify: `ai-news-crawler/api/articles.py` (article_detail에 UserNote 추가)

- [ ] **Step 1: article_detail 라우터에 UserNote 추가**

`api/articles.py`의 `article_detail()` 함수에 추가:

```python
    article.tags_list = json.loads(article.tags or "[]")
    article.breakdown = json.loads(article.score_breakdown or "{}")
    article.user_note = db.query(UserNote).filter_by(article_id=article_id).first()
```

- [ ] **Step 2: article.html 업데이트**

`ui/templates/article.html`을 다음으로 교체:

```html
{% extends "base.html" %}
{% set active_page = 'feed' %}
{% block content %}
{% set note = article.user_note %}

<div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-3 flex-shrink-0">
  <a href="/" class="text-sm text-slate-500 hover:text-slate-700">← 피드</a>
  <span class="text-slate-300">|</span>
  <span class="text-sm text-slate-500">{{ article.source.name }}</span>
  <span class="text-sm {{ '🇰🇷' if article.source.country == 'kr' else '🌏' }}">
    {{ '🇰🇷 한국' if article.source.country == 'kr' else '🌏 해외' }}
  </span>
</div>

<div class="flex-1 overflow-y-auto p-8 max-w-3xl mx-auto w-full">
  <!-- 제목 + 스코어 -->
  <div class="flex justify-between items-start gap-4 mb-3">
    <h1 class="text-xl font-bold text-slate-800 leading-snug flex-1">{{ article.title }}</h1>
    <span class="text-sm font-bold px-3 py-1 rounded-full text-white flex-shrink-0
                 {% if article.score >= 90 %}bg-blue-600{% elif article.score >= 70 %}bg-emerald-600{% else %}bg-violet-600{% endif %}">
      {{ article.score }}점
    </span>
  </div>

  <!-- 메타 -->
  <div class="text-sm text-slate-500 mb-4 flex items-center gap-2">
    <span>{{ article.source.name }}</span>
    {% if article.published_at %}<span>· {{ article.published_at.strftime('%Y-%m-%d') }}</span>{% endif %}
  </div>

  <!-- 태그 -->
  <div class="flex flex-wrap gap-1.5 mb-4">
    {% for tag in article.tags_list %}
    <span class="bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
    {% endfor %}
    {% if note %}{% for tag in note.user_tags | from_json %}
    <span class="bg-yellow-50 text-yellow-700 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
    {% endfor %}{% endif %}
  </div>

  <!-- 액션 -->
  <div class="flex items-center gap-2 mb-6">
    <button class="text-xs px-3 py-1.5 rounded border {% if note and note.is_bookmarked %}border-yellow-300 bg-yellow-50 text-yellow-700{% else %}border-slate-200 text-slate-500 hover:bg-slate-50{% endif %}"
            hx-post="/articles/{{ article.id }}/bookmark"
            hx-swap="outerHTML">
      {{ '🔖 북마크됨' if note and note.is_bookmarked else '☆ 북마크' }}
    </button>
    <button class="text-xs px-3 py-1.5 rounded border border-slate-200 text-slate-500 hover:bg-slate-50"
            hx-post="/articles/{{ article.id }}/read"
            hx-swap="outerHTML">
      {{ '↩ 읽음취소' if article.is_read else '✓ 읽음' }}
    </button>
    <a href="{{ article.url }}" target="_blank"
       class="ml-auto px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg">
      원문 보기 →
    </a>
  </div>

  <!-- 본문 요약 -->
  <div class="bg-slate-50 rounded-lg p-4 text-sm text-slate-700 leading-relaxed mb-4">
    {{ article.content }}
  </div>

  <!-- 번역 (해외 아티클만) -->
  {% if article.source.country == 'global' %}
  <div class="mb-4">
    <button class="text-sm px-3 py-1.5 rounded border border-blue-200 text-blue-600 hover:bg-blue-50"
            hx-post="/articles/{{ article.id }}/translate"
            hx-target="#translation-{{ article.id }}"
            hx-swap="outerHTML"
            hx-indicator="#translate-spinner">
      한글 요약 보기
    </button>
    <span id="translate-spinner" class="htmx-indicator text-xs text-slate-400 ml-2">번역 중...</span>
    <div id="translation-{{ article.id }}" class="mt-2"></div>
  </div>
  {% endif %}

  <!-- 메모 -->
  <div class="mb-4" id="memo-{{ article.id }}">
    {% if note and note.memo %}
    <div class="bg-yellow-50 border-l-2 border-yellow-400 px-3 py-2 rounded-r text-sm text-slate-700">
      📝 {{ note.memo }}
    </div>
    <button class="text-xs text-slate-400 hover:text-slate-600 mt-1"
            hx-get="/articles/{{ article.id }}/memo-form"
            hx-target="#memo-{{ article.id }}"
            hx-swap="outerHTML">수정</button>
    {% else %}
    <button class="text-sm text-slate-400 hover:text-slate-600 border border-dashed border-slate-200 px-3 py-1.5 rounded"
            hx-get="/articles/{{ article.id }}/memo-form"
            hx-target="#memo-{{ article.id }}"
            hx-swap="outerHTML">📝 메모 추가</button>
    {% endif %}
  </div>

  <!-- 커스텀 태그 -->
  <div id="user-tags-{{ article.id }}" class="flex items-center gap-1 flex-wrap">
    {% if note %}{% for tag in note.user_tags | from_json %}
    <span class="bg-yellow-50 text-yellow-700 text-xs px-2 py-0.5 rounded">{{ tag }}</span>
    {% endfor %}{% endif %}
    <button class="text-xs px-2 py-1 rounded border border-dashed border-slate-200 text-slate-400 hover:bg-slate-50"
            hx-get="/articles/{{ article.id }}/tags-form"
            hx-target="#user-tags-{{ article.id }}"
            hx-swap="outerHTML">+태그</button>
  </div>

  <!-- 스코어 상세 -->
  <details class="mt-6 text-sm">
    <summary class="text-slate-500 cursor-pointer hover:text-slate-700">스코어 상세 ({{ article.score }}점)</summary>
    <ul class="mt-2 text-slate-600 space-y-1 pl-4">
      <li>출처 가중치: {{ article.breakdown.source }}점</li>
      <li>최신성: {{ article.breakdown.recency }}점</li>
      <li>키워드 매칭: {{ article.breakdown.keyword }}점</li>
    </ul>
  </details>
</div>
{% endblock %}
```

- [ ] **Step 3: sources.html에 country 컬럼 추가**

`ui/templates/sources.html`을 다음으로 교체:

```html
{% extends "base.html" %}
{% set active_page = 'sources' %}
{% block content %}
<div class="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4 flex-shrink-0">
  <h1 class="text-lg font-bold text-slate-800">📡 소스 관리</h1>
  <span class="text-sm text-slate-400">{{ sources|length }}개</span>
</div>

<div class="flex-1 overflow-auto p-6">
  <table class="w-full text-sm bg-white rounded-xl border border-slate-200 overflow-hidden">
    <thead class="bg-slate-50 text-slate-500 text-xs uppercase">
      <tr>
        <th class="px-4 py-3 text-left">소스</th>
        <th class="px-4 py-3 text-left">국가</th>
        <th class="px-4 py-3 text-left">타입</th>
        <th class="px-4 py-3 text-left">가중치</th>
        <th class="px-4 py-3 text-left">마지막 크롤링</th>
        <th class="px-4 py-3 text-left">상태</th>
        <th class="px-4 py-3 text-left">실패</th>
        <th class="px-4 py-3 text-left">액션</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-slate-100">
      {% for source in sources %}
      <tr class="hover:bg-slate-50 {% if not source.is_active %}opacity-50{% endif %}">
        <td class="px-4 py-3 font-medium text-slate-700">{{ source.name }}</td>
        <td class="px-4 py-3 text-slate-500">{{ '🇰🇷 한국' if source.country == 'kr' else '🌏 해외' }}</td>
        <td class="px-4 py-3 text-slate-500">{{ source.type }}</td>
        <td class="px-4 py-3 text-slate-500">{{ source.weight }}</td>
        <td class="px-4 py-3 text-slate-500 text-xs">
          {{ source.last_crawled_at.strftime('%m-%d %H:%M') if source.last_crawled_at else '-' }}
        </td>
        <td class="px-4 py-3">
          <span class="text-xs px-2 py-0.5 rounded-full {% if source.is_active %}bg-green-100 text-green-700{% else %}bg-slate-100 text-slate-500{% endif %}">
            {{ '활성' if source.is_active else '비활성' }}
          </span>
        </td>
        <td class="px-4 py-3 text-slate-500 text-xs">
          {% set failures = failure_map.get(source.id, []) %}
          {{ failures|length }}건
          {% if failures %}
          <button class="ml-1 text-xs px-2 py-0.5 rounded border border-orange-200 text-orange-600 hover:bg-orange-50"
                  hx-post="/sources/{{ source.id }}/retry"
                  hx-swap="outerHTML">재시도</button>
          {% endif %}
        </td>
        <td class="px-4 py-3">
          <button class="text-xs px-2 py-1 rounded border border-slate-200 text-slate-500 hover:bg-slate-50"
                  hx-post="/sources/{{ source.id }}/toggle"
                  hx-swap="outerHTML">
            {{ '비활성화' if source.is_active else '활성화' }}
          </button>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
```

- [ ] **Step 4: 커밋**

```bash
git add ai-news-crawler/ui/templates/article.html ai-news-crawler/ui/templates/sources.html ai-news-crawler/api/articles.py
git commit -m "feat: 아티클 상세·소스 관리 페이지 Tailwind 재설계, 번역 버튼 추가"
```

---

## Task 13: 전체 테스트 및 동작 확인

**Files:** 없음 (검증만)

- [ ] **Step 1: 전체 테스트 실행**

```bash
cd ai-news-crawler && python -m pytest tests/ -v
```

Expected: 전체 PASS

- [ ] **Step 2: 서버 기동 및 전체 기능 확인**

```bash
cd ai-news-crawler && uvicorn main:app --reload --port 8000
```

확인 항목:
- http://localhost:8000 → 피드 (사이드바, 국가 탭)
- http://localhost:8000/bookmarks → 북마크 페이지
- http://localhost:8000/search → 검색 페이지
- http://localhost:8000/sources → 31개 소스 표시 (국가 컬럼 포함)
- 크롤링 버튼 → 사이드바에서 실행
- 아티클 카드 → 북마크, 메모, 읽음 토글

- [ ] **Step 3: 최종 커밋**

```bash
git add -A
git commit -m "chore: AI 아카이브 고도화 완료 — 소스 31개, 북마크/메모/태그/검색/번역"
```
