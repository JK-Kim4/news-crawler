import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.api.templates import templates
from app.auth.dependencies import require_admin
from app.db.models import Article, CrawlFailure, ScoringWeight, Source, User
from app.db.session import get_db

router = APIRouter(prefix="/admin")
logger = logging.getLogger(__name__)


@router.get("/sources", response_class=HTMLResponse)
def admin_sources(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.name).all()
    return templates.TemplateResponse(request, "admin/sources.html", {"request": request, "sources": sources})

@router.post("/sources")
def admin_create_source(name: str = Form(...), url: str = Form(...), source_type: str = Form("scraper"),
                        category: str = Form("article"), weight: float = Form(5.0), country: str = Form("kr"),
                        user: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.add(Source(name=name, url=url, type=source_type, category=category, weight=weight, country=country))
    db.commit()
    return RedirectResponse(url="/admin/sources", status_code=303)

@router.post("/sources/{sid}/delete")
def admin_delete_source(sid: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = db.query(Source).filter_by(id=sid).first()
    if s:
        db.delete(s)
        db.commit()
    return RedirectResponse(url="/admin/sources", status_code=303)

@router.post("/articles/{aid}/delete")
def admin_delete_article(aid: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    a = db.query(Article).filter_by(id=aid).first()
    if a:
        a.is_deleted = True
        db.commit()
    return JSONResponse({"status": "deleted"})

@router.post("/articles/{aid}/score")
def admin_update_score(aid: int, score: float = Form(...), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    a = db.query(Article).filter_by(id=aid).first()
    if not a:
        raise HTTPException(404)
    a.score = int(score)
    db.commit()
    return JSONResponse({"status": "updated", "score": a.score})

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/users.html", {"request": request, "users": users, "current_user": user})

@router.post("/users/{uid}/role")
def admin_update_role(uid: int, role: str = Form(...), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if role not in {"admin", "user"}:
        raise HTTPException(400, "Invalid role")
    if uid == user.id and role != "admin":
        raise HTTPException(400, "관리자는 자신의 권한을 해제할 수 없습니다.")
    t = db.query(User).filter_by(id=uid).first()
    if t:
        t.role = role
        db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/users/{uid}/active")
def admin_toggle_active(uid: int, is_active: bool = Form(False), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if uid == user.id:
        raise HTTPException(400, "자신의 계정을 비활성화할 수 없습니다.")
    t = db.query(User).filter_by(id=uid).first()
    if t:
        t.is_active = is_active
        db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/scoring-weights", response_class=HTMLResponse)
def admin_weights(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    weights = db.query(ScoringWeight).order_by(ScoringWeight.key).all()
    return templates.TemplateResponse(request, "admin/weights.html", {"request": request, "weights": weights})

@router.post("/scoring-weights/{key}")
def admin_update_weight(key: str, weight: float = Form(...), user: User = Depends(require_admin), db: Session = Depends(get_db)):
    sw = db.query(ScoringWeight).filter_by(key=key).first()
    if not sw:
        raise HTTPException(404)
    sw.weight = weight
    sw.updated_at = datetime.now(timezone.utc)
    db.commit()
    return RedirectResponse(url="/admin/scoring-weights", status_code=303)

@router.get("/crawl-failures", response_class=HTMLResponse)
def admin_failures(request: Request, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    failures = db.query(CrawlFailure).filter(CrawlFailure.resolved_at.is_(None)).order_by(CrawlFailure.failed_at.desc()).all()
    return templates.TemplateResponse(request, "admin/alerts.html", {"request": request, "failures": failures})

@router.get("/crawl-failures/count")
def admin_failure_count(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return JSONResponse({"count": db.query(CrawlFailure).filter(CrawlFailure.resolved_at.is_(None)).count()})

@router.post("/crawl-failures/{fid}/resolve")
def admin_resolve(fid: int, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    f = db.query(CrawlFailure).filter_by(id=fid).first()
    if f:
        f.resolved_at = datetime.now(timezone.utc)
        db.commit()
    return RedirectResponse(url="/admin/crawl-failures", status_code=303)
