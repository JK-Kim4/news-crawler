import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from app.api.templates import templates
from app.auth.dependencies import get_current_user
from app.db.models import Article, Like, Scrap, Source
from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_json(val):
    try:
        r = json.loads(val or "[]")
        return r if isinstance(r, list) else []
    except (TypeError, ValueError):
        return []


def _enrich(article, user):
    article.tags_list = _parse_json(article.tags)
    article.breakdown = json.loads(article.score_breakdown or "{}")
    user_id = user.id if user else None
    article.user_liked = False
    article.user_scrapped = False
    if user_id:
        from sqlalchemy.orm import object_session
        db = object_session(article)
        if db:
            article.user_liked = db.query(Like.id).filter_by(user_id=user_id, article_id=article.id).first() is not None
            article.user_scrapped = db.query(Scrap.id).filter_by(user_id=user_id, article_id=article.id).first() is not None
    return article


def _article_query(db: Session):
    return (
        db.query(Article)
        .options(joinedload(Article.source))
        .join(Source)
        .filter(Source.is_active.is_(True), Article.is_deleted.is_(False))
    )


@router.get("/", response_class=HTMLResponse)
def feed(
    request: Request,
    sort: str = "score",
    country: str = "",
    category: str = "",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    query = _article_query(db)
    if category in {"article", "paper", "blog"}:
        query = query.filter(Article.category == category)
    if country in {"kr", "global"}:
        query = query.filter(Source.country == country)
    if sort == "date":
        query = query.order_by(Article.published_at.desc(), Article.id.desc())
    else:
        query = query.order_by(Article.score.desc(), Article.published_at.desc())

    total = query.count()
    articles = [_enrich(a, user) for a in query.offset((page - 1) * size).limit(size).all()]
    total_pages = max(1, (total + size - 1) // size)

    return templates.TemplateResponse(request, "feed.html", {
        "request": request, "articles": articles, "sort": sort,
        "selected_country": country, "selected_category": category,
        "page": page, "total_pages": total_pages, "total": total,
    })


@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = "",
    category: str = "",
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    articles = []
    if q.strip():
        terms = [t.strip() for t in q.split() if t.strip()]
        fts_query = " AND ".join(f'"{t}"' for t in terms)
        sql = """
            SELECT articles.id FROM article_fts
            JOIN articles ON articles.id = article_fts.rowid
            JOIN sources ON sources.id = articles.source_id
            WHERE article_fts MATCH :query AND sources.is_active = 1
              AND COALESCE(articles.is_deleted, 0) = 0
        """
        params = {"query": fts_query}
        if category in {"article", "paper", "blog"}:
            sql += " AND articles.category = :category"
            params["category"] = category
        sql += " ORDER BY bm25(article_fts) LIMIT 50"
        ids = db.execute(text(sql), params).scalars().all()
        if ids:
            article_map = {a.id: a for a in db.query(Article).options(joinedload(Article.source)).filter(Article.id.in_(ids)).all()}
            articles = [_enrich(article_map[i], user) for i in ids if i in article_map]

    return templates.TemplateResponse(request, "search.html", {
        "request": request, "articles": articles, "query": q, "selected_category": category,
    })


@router.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    article = db.query(Article).options(joinedload(Article.source)).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article = _enrich(article, user)
    return templates.TemplateResponse(request, "article.html", {"request": request, "article": article})
