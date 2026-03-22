from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.auth.dependencies import require_login
from app.db.models import Article, Like, User
from app.db.session import get_db

router = APIRouter()


@router.post("/articles/{article_id}/like", response_class=HTMLResponse)
def toggle_like(article_id: int, user: User = Depends(require_login), db: Session = Depends(get_db)):
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        return HTMLResponse("Not found", status_code=404)
    existing = db.query(Like).filter_by(user_id=user.id, article_id=article_id).first()
    if existing:
        db.delete(existing)
        article.like_count = max(0, article.like_count - 1)
        liked = False
    else:
        db.add(Like(user_id=user.id, article_id=article_id))
        article.like_count += 1
        liked = True
    db.commit()
    cls = "border-red-300 bg-red-50 text-red-600" if liked else "border-slate-200 text-slate-500 hover:bg-slate-50"
    return HTMLResponse(
        f'<button class="text-xs px-2 py-1 rounded border {cls} flex items-center gap-1" '
        f'hx-post="/articles/{article_id}/like" hx-swap="outerHTML">'
        f'{"♥" if liked else "♡"} {article.like_count}</button>'
    )
