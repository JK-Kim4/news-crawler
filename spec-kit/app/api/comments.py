from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.api.templates import templates
from app.auth.dependencies import get_current_user, require_login
from app.db.models import Article, Comment, User
from app.db.session import get_db

router = APIRouter()


@router.get("/articles/{article_id}/comments", response_class=HTMLResponse)
def list_comments(request: Request, article_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request)
    comments = db.query(Comment).filter_by(article_id=article_id).order_by(Comment.created_at.asc()).all()
    for c in comments:
        _ = c.user
    return templates.TemplateResponse(request, "partials/_comments.html",
        {"request": request, "comments": comments, "article_id": article_id, "user": user})


@router.post("/articles/{article_id}/comments", response_class=HTMLResponse)
def create_comment(request: Request, article_id: int, content: str = Form(...),
                   user: User = Depends(require_login), db: Session = Depends(get_db)):
    content = content.strip()
    if not content or len(content) > 1000:
        raise HTTPException(status_code=400, detail="댓글은 1~1000자 이내로 작성해주세요.")
    article = db.query(Article).filter_by(id=article_id).first()
    if not article:
        raise HTTPException(status_code=404)
    db.add(Comment(user_id=user.id, article_id=article_id, content=content))
    article.comment_count += 1
    db.commit()
    comments = db.query(Comment).filter_by(article_id=article_id).order_by(Comment.created_at.asc()).all()
    for c in comments:
        _ = c.user
    return templates.TemplateResponse(request, "partials/_comments.html",
        {"request": request, "comments": comments, "article_id": article_id, "user": user})


@router.post("/comments/{comment_id}/edit", response_class=HTMLResponse)
def edit_comment(request: Request, comment_id: int, content: str = Form(...),
                 user: User = Depends(require_login), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404)
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="본인의 댓글만 수정할 수 있습니다.")
    content = content.strip()
    if not content or len(content) > 1000:
        raise HTTPException(status_code=400)
    comment.content = content
    comment.is_edited = True
    comment.updated_at = datetime.now(timezone.utc)
    db.commit()
    comments = db.query(Comment).filter_by(article_id=comment.article_id).order_by(Comment.created_at.asc()).all()
    for c in comments:
        _ = c.user
    return templates.TemplateResponse(request, "partials/_comments.html",
        {"request": request, "comments": comments, "article_id": comment.article_id, "user": user})


@router.post("/comments/{comment_id}/delete", response_class=HTMLResponse)
def delete_comment(request: Request, comment_id: int, user: User = Depends(require_login), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404)
    if comment.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    article = db.query(Article).filter_by(id=comment.article_id).first()
    aid = comment.article_id
    db.delete(comment)
    if article:
        article.comment_count = max(0, article.comment_count - 1)
    db.commit()
    comments = db.query(Comment).filter_by(article_id=aid).order_by(Comment.created_at.asc()).all()
    for c in comments:
        _ = c.user
    return templates.TemplateResponse(request, "partials/_comments.html",
        {"request": request, "comments": comments, "article_id": aid, "user": user})
