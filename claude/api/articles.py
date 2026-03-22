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
from auth.dependencies import require_login, require_admin
from crawler.runner import CrawlRunner, get_crawl_status
from db.models import Article, Source, User, UserNote
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
    user = getattr(getattr(request, 'state', None), 'user', None)
    return {"request": request, **build_sidebar_context(db, user)}


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
    user = getattr(getattr(request, 'state', None), 'user', None)
    user_id = user.id if user else None

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

    articles = enrich_articles(query.limit(50).all(), user_id)
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
    user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    memo_first = case((UserNote.memo.is_not(None), 0), else_=1)
    articles = (
        _apply_country_filter(_article_query(db).join(UserNote), country)
        .filter(UserNote.is_bookmarked.is_(True), UserNote.user_id == user.id)
        .order_by(memo_first.asc(), Article.published_at.desc(), Article.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "bookmarks.html",
        {
            **_base_context(request, db),
            "articles": enrich_articles(articles, user.id),
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
    user = getattr(getattr(request, 'state', None), 'user', None)
    user_id = user.id if user else None

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
    articles = enrich_articles(
        [article_map[article_id] for article_id in article_ids if article_id in article_map],
        user_id,
    )

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
    user = getattr(getattr(request, 'state', None), 'user', None)
    user_id = user.id if user else None

    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article = enrich_article(article, user_id)
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
def toggle_bookmark(
    request: Request,
    article_id: int,
    user: User = Depends(require_login),
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
    note = get_or_create_user_note(db, article, user.id)
    note.is_bookmarked = not note.is_bookmarked
    db.commit()
    is_bm = note.is_bookmarked
    return HTMLResponse(
        f'<button class="text-xs px-2 py-1 rounded border '
        f'{"border-yellow-300 bg-yellow-50 text-yellow-700" if is_bm else "border-slate-200 text-slate-500 hover:bg-slate-50"}" '
        f'hx-post="/articles/{article_id}/bookmark" '
        f'hx-swap="outerHTML">'
        f'{"🔖 북마크됨" if is_bm else "☆ 북마크"}'
        f'</button>'
    )


@router.get("/articles/{article_id}/memo-form", response_class=HTMLResponse)
def memo_form(
    article_id: int,
    user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    note = db.query(UserNote).filter_by(article_id=article_id, user_id=user.id).first()
    current = (note.memo or "") if note else ""
    return HTMLResponse(
        f'<form id="memo-{article_id}" '
        f'hx-post="/articles/{article_id}/memo" '
        f'hx-target="#memo-{article_id}" '
        f'hx-swap="outerHTML">'
        f'<textarea name="memo" rows="3" '
        f'class="w-full border border-slate-200 rounded px-2 py-1 text-sm mt-1">{current}</textarea>'
        f'<div class="flex gap-2 mt-1">'
        f'<button type="submit" class="text-xs px-2 py-1 bg-blue-600 text-white rounded">저장</button>'
        f'<button type="button" class="text-xs px-2 py-1 border border-slate-200 rounded text-slate-500" '
        f'onclick="this.closest(\'form\').outerHTML=\'\'">취소</button>'
        f'</div>'
        f'</form>'
    )


@router.get("/articles/{article_id}/tags-form", response_class=HTMLResponse)
def tags_form(
    article_id: int,
    user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    note = db.query(UserNote).filter_by(article_id=article_id, user_id=user.id).first()
    current = ",".join(json.loads(note.user_tags)) if note and note.user_tags else ""
    return HTMLResponse(
        f'<form id="user-tags-{article_id}" '
        f'hx-post="/articles/{article_id}/tags" '
        f'hx-target="#user-tags-{article_id}" '
        f'hx-swap="outerHTML" '
        f'class="flex items-center gap-1">'
        f'<input name="user_tags" value="{current}" placeholder="태그1,태그2" '
        f'class="border border-slate-200 rounded px-2 py-1 text-xs" style="width:180px">'
        f'<button type="submit" class="text-xs px-2 py-1 bg-blue-600 text-white rounded">저장</button>'
        f'</form>'
    )


@router.post("/articles/{article_id}/memo", response_class=HTMLResponse)
def save_memo(
    request: Request,
    article_id: int,
    memo: str = Form(default=""),
    user: User = Depends(require_login),
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
    note = get_or_create_user_note(db, article, user.id)
    cleaned = memo.strip()
    note.memo = cleaned or None
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_archive_panel.html",
        {"request": request, "article": enrich_article(article, user.id)},
    )


@router.post("/articles/{article_id}/tags", response_class=HTMLResponse)
def save_tags(
    request: Request,
    article_id: int,
    user_tags: str = Form(default=""),
    user: User = Depends(require_login),
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
    note = get_or_create_user_note(db, article, user.id)
    note.user_tags = json.dumps(parse_user_tags_input(user_tags), ensure_ascii=False)
    db.commit()
    db.refresh(article)
    return templates.TemplateResponse(
        request,
        "_archive_panel.html",
        {"request": request, "article": enrich_article(article, user.id)},
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
    user = getattr(getattr(request, 'state', None), 'user', None)
    user_id = user.id if user else None

    article = (
        db.query(Article)
        .options(joinedload(Article.source), joinedload(Article.user_note))
        .filter(Article.id == article_id)
        .first()
    )
    if not article:
        return JSONResponse({"error": "not found"}, status_code=404)
    article = enrich_article(article, user_id)
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


@router.get("/api/crawl/status")
def crawl_status():
    return JSONResponse({"is_crawling": get_crawl_status()})


@router.post("/api/crawl", response_class=HTMLResponse)
def manual_crawl(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    runner = CrawlRunner(db)
    result = runner.run()
    if result.get("status") == "already_running":
        return HTMLResponse(
            '<span class="text-amber-400">이미 크롤링이 진행 중입니다.</span>',
            status_code=409,
        )
    crawled = result.get("crawled", 0)
    failed = result.get("failed", 0)
    return HTMLResponse(
        f'<span class="text-emerald-400">{crawled}건 수집</span>'
        + (f' · <span class="text-red-400">{failed}건 실패</span>' if failed else "")
    )
