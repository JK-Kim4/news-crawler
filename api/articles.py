import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import case, text
from sqlalchemy.orm import Session, joinedload
from deep_translator import GoogleTranslator
from api.helpers import (
    build_sidebar_context,
    enrich_article,
    enrich_articles,
    get_or_create_user_note,
    parse_user_tags_input,
)
from api.templates import templates
from crawler.runner import CrawlRunner
from db.models import Article, Source, UserNote
from db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)
translator_pool = ThreadPoolExecutor(max_workers=4)


def _article_query(db: Session):
    return (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .join(Source)
        .filter(Source.is_active.is_(True))
    )


def _apply_country_filter(query, country: str):
    if country in {"kr", "global"}:
        query = query.filter(Source.country == country)
    return query


def _base_context(request: Request, db: Session):
    return {"request": request, **build_sidebar_context(db)}


def _build_fts_query(raw_query: str) -> str:
    terms = [term.strip() for term in raw_query.split() if term.strip()]
    escaped = [f'"{term.replace("\"", "\"\"")}"' for term in terms]
    return " AND ".join(escaped)


def _translate_text(text_value: str) -> str:
    translator = GoogleTranslator(source="auto", target="ko")
    return translator.translate(text_value)


@router.get("/", response_class=HTMLResponse)
def feed(
    request: Request,
    sort: str = "score",
    country: str = "",
    source_id: int | None = None,
    tag: str | None = None,
    unread: bool = False,
    db: Session = Depends(get_db),
):
    query = _apply_country_filter(_article_query(db), country)
    if source_id:
        query = query.filter(Article.source_id == source_id)
    if tag:
        query = query.filter(Article.tags.contains(tag))
    if unread:
        query = query.filter(Article.is_read.is_(False))
    if sort == "date":
        query = query.order_by(Article.published_at.desc(), Article.id.desc())
    else:
        query = query.order_by(Article.score.desc(), Article.published_at.desc(), Article.id.desc())

    articles = enrich_articles(query.limit(50).all())
    sources = db.query(Source).filter(Source.is_active.is_(True)).order_by(Source.country, Source.name).all()

    return templates.TemplateResponse(
        request,
        "feed.html",
        {
            **_base_context(request, db),
            "articles": articles,
            "sources": sources,
            "sort": sort,
            "selected_country": country,
            "selected_source_id": source_id,
            "selected_tag": tag,
            "unread_only": unread,
        },
    )


@router.get("/bookmarks", response_class=HTMLResponse)
def bookmarks_page(
    request: Request,
    country: str = "all",
    db: Session = Depends(get_db),
):
    memo_first = case((UserNote.memo.is_not(None), 0), else_=1)
    articles = (
        _apply_country_filter(_article_query(db).join(UserNote), country)
        .filter(UserNote.is_bookmarked.is_(True))
        .order_by(memo_first.asc(), Article.published_at.desc(), Article.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "bookmarks.html",
        {
            **_base_context(request, db),
            "articles": enrich_articles(articles),
            "selected_country": country,
        },
    )


@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = "",
    country: str = "all",
    db: Session = Depends(get_db),
):
    article_ids = []
    query_text = _build_fts_query(q.strip())
    if query_text:
        sql = """
            SELECT articles.id
            FROM article_fts
            JOIN articles ON articles.id = article_fts.rowid
            JOIN sources ON sources.id = articles.source_id
            WHERE article_fts MATCH :query
              AND sources.is_active = 1
        """
        params = {"query": query_text}
        if country in {"kr", "global"}:
            sql += " AND sources.country = :country"
            params["country"] = country
        sql += " ORDER BY bm25(article_fts), articles.published_at DESC, articles.id DESC LIMIT 50"
        article_ids = db.execute(text(sql), params).scalars().all()

    article_map = {
        article.id: article
        for article in (
            db.query(Article)
            .options(joinedload(Article.source), joinedload(Article.user_note))
            .filter(Article.id.in_(article_ids))
            .all()
            if article_ids
            else []
        )
    }
    articles = enrich_articles([article_map[article_id] for article_id in article_ids if article_id in article_map])

    return templates.TemplateResponse(
        request,
        "search.html",
        {
            **_base_context(request, db),
            "articles": articles,
            "query": q,
            "selected_country": country,
        },
    )


@router.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article = enrich_article(article)
    article.breakdown = json.loads(article.score_breakdown or "{}")
    return templates.TemplateResponse(
        request,
        "article.html",
        {
            **_base_context(request, db),
            "article": article,
        },
    )


@router.post("/articles/{article_id}/bookmark", response_class=HTMLResponse)
def toggle_bookmark(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = get_or_create_user_note(db, article)
    note.is_bookmarked = not note.is_bookmarked
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_archive_panel.html",
        {"request": request, "article": enrich_article(article)},
    )


@router.post("/articles/{article_id}/memo", response_class=HTMLResponse)
def save_memo(
    request: Request,
    article_id: int,
    memo: str = Form(default=""),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = get_or_create_user_note(db, article)
    cleaned = memo.strip()
    note.memo = cleaned or None
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_archive_panel.html",
        {"request": request, "article": enrich_article(article)},
    )


@router.post("/articles/{article_id}/tags", response_class=HTMLResponse)
def save_tags(
    request: Request,
    article_id: int,
    user_tags: str = Form(default=""),
    db: Session = Depends(get_db),
):
    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    note = get_or_create_user_note(db, article)
    note.user_tags = json.dumps(parse_user_tags_input(user_tags), ensure_ascii=False)
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_archive_panel.html",
        {"request": request, "article": enrich_article(article)},
    )


@router.post("/articles/{article_id}/read", response_class=HTMLResponse)
def toggle_read(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    article.is_read = not article.is_read
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_read_button.html",
        {"request": request, "article": article},
    )


@router.post("/articles/{article_id}/translate", response_class=HTMLResponse)
def translate_article(request: Request, article_id: int, db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    article = enrich_article(article)
    if article.country == "kr":
        return HTMLResponse("한국어 원문은 번역 대상이 아닙니다.", status_code=400)

    excerpt = (article.content or "").strip()[:500]
    parts = [f"제목: {article.title.strip()}"]
    if excerpt:
        parts.append(f"본문: {excerpt}")
    payload = "\n\n".join(parts)

    translated_text = None
    translation_error = None
    future = translator_pool.submit(_translate_text, payload)
    try:
        translated_text = future.result(timeout=5)
    except FuturesTimeoutError:
        future.cancel()
        translation_error = "번역을 가져올 수 없습니다."
    except Exception as exc:
        logger.warning("Translation failed for article %s: %s", article.id, exc)
        translation_error = "번역을 가져올 수 없습니다."

    return templates.TemplateResponse(
        request,
        "_translation_result.html",
        {
            "request": request,
            "translated_text": translated_text,
            "translation_error": translation_error,
        },
    )


@router.post("/api/crawl")
def manual_crawl(db: Session = Depends(get_db)):
    runner = CrawlRunner(db)
    result = runner.run()
    if result.get("status") == "already_running":
        return JSONResponse({"status": "already_running"}, status_code=409)
    return JSONResponse(result, status_code=200)
