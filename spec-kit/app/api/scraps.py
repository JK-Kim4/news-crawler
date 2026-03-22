from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from app.api.templates import templates
from app.auth.dependencies import require_login, get_current_user
from app.db.models import Article, Scrap, Source, User
from app.db.session import get_db

router = APIRouter()


@router.post("/articles/{article_id}/scrap", response_class=HTMLResponse)
def toggle_scrap(article_id: int, user: User = Depends(require_login), db: Session = Depends(get_db)):
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return HTMLResponse("Not found", status_code=404)
    existing = db.query(Scrap).filter_by(user_id=user.id, article_id=article_id).first()
    if existing:
        db.delete(existing)
        scrapped = False
    else:
        db.add(Scrap(user_id=user.id, article_id=article_id))
        scrapped = True
    db.commit()
    cls = "border-yellow-300 bg-yellow-50 text-yellow-700" if scrapped else "border-slate-200 text-slate-500 hover:bg-slate-50"
    return HTMLResponse(
        f'<button class="text-xs px-2 py-1 rounded border {cls}" '
        f'hx-post="/articles/{article_id}/scrap" hx-swap="outerHTML">'
        f'{"🔖 스크랩됨" if scrapped else "☆ 스크랩"}</button>'
    )


@router.get("/my/scraps", response_class=HTMLResponse)
def my_scraps(request: Request, page: int = 1, size: int = 20,
              user: User = Depends(require_login), db: Session = Depends(get_db)):
    from app.api.articles import _enrich
    query = (
        db.query(Article).join(Scrap).options(joinedload(Article.source))
        .filter(Scrap.user_id == user.id, Article.is_deleted.is_(False))
        .order_by(Scrap.created_at.desc())
    )
    total = query.count()
    articles = [_enrich(a, user) for a in query.offset((page - 1) * size).limit(size).all()]
    total_pages = max(1, (total + size - 1) // size)
    return templates.TemplateResponse(request, "my_scraps.html", {
        "request": request, "articles": articles, "page": page,
        "total_pages": total_pages, "total": total,
    })
