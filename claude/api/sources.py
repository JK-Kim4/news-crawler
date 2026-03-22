import math
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from api.helpers import build_sidebar_context
from api.templates import templates
from auth.dependencies import require_admin
from crawler.runner import CrawlRunner
from db.models import CrawlFailure, Source, User
from db.session import get_db

router = APIRouter()

SOURCES_PER_PAGE = 15


def _build_sources_query(db: Session, q: str, country: str, status: str):
    query = db.query(Source)
    if q:
        query = query.filter(Source.name.ilike(f"%{q}%"))
    if country in {"kr", "global"}:
        query = query.filter(Source.country == country)
    if status == "active":
        query = query.filter(Source.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(Source.is_active.is_(False))
    return query.order_by(Source.country, Source.name)


def _build_failure_map(db: Session):
    failures = (
        db.query(CrawlFailure)
        .filter(CrawlFailure.resolved_at.is_(None))
        .all()
    )
    failure_map = {}
    for failure in failures:
        failure_map.setdefault(failure.source_id, []).append(failure)
    return failure_map


def _sources_context(db, q, country, status, page):
    query = _build_sources_query(db, q, country, status)
    total = query.count()
    total_pages = max(1, math.ceil(total / SOURCES_PER_PAGE))
    page = max(1, min(page, total_pages))
    sources = query.offset((page - 1) * SOURCES_PER_PAGE).limit(SOURCES_PER_PAGE).all()
    return {
        "sources": sources,
        "failure_map": _build_failure_map(db),
        "q": q,
        "selected_country": country,
        "selected_status": status,
        "page": page,
        "total_pages": total_pages,
        "total": total,
    }


@router.get("/sources", response_class=HTMLResponse)
def sources_page(
    request: Request,
    q: str = "",
    country: str = "",
    status: str = "",
    page: int = 1,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ctx = _sources_context(db, q, country, status, page)
    # HTMX partial: return only table fragment
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request, "_sources_table.html", {"request": request, **ctx},
        )
    user_for_sidebar = getattr(getattr(request, 'state', None), 'user', None)
    return templates.TemplateResponse(
        request,
        "sources.html",
        {
            "request": request,
            **ctx,
            **build_sidebar_context(db, user_for_sidebar),
        },
    )


@router.post("/sources/{source_id}/toggle")
def toggle_source(
    source_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    source = db.query(Source).filter_by(id=source_id).first()
    if not source:
        return JSONResponse({"error": "not found"}, status_code=404)
    source.is_active = not source.is_active
    db.commit()
    label = "비활성화" if source.is_active else "활성화"
    button_class = (
        "inline-flex items-center rounded-full bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white"
    )
    return HTMLResponse(
        f'<button class="{button_class}" hx-post="/sources/{source_id}/toggle" hx-swap="outerHTML">{label}</button>'
    )


@router.post("/sources/{source_id}/retry")
def retry_source(
    source_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    source = db.query(Source).filter_by(id=source_id).first()
    if not source:
        return JSONResponse({"error": "not found"}, status_code=404)

    failures = (
        db.query(CrawlFailure)
        .filter(
            CrawlFailure.source_id == source_id,
            CrawlFailure.resolved_at.is_(None),
        )
        .all()
    )
    for failure in failures:
        failure.failed_at = datetime.now(timezone.utc) - timedelta(hours=7)
    db.commit()
    CrawlRunner(db).run()
    return HTMLResponse('<span class="text-sm font-medium text-emerald-700">재시도 완료</span>')
