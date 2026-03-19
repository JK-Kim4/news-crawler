from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from api.helpers import build_sidebar_context
from api.templates import templates
from crawler.runner import CrawlRunner
from db.models import CrawlFailure, Source
from db.session import get_db

router = APIRouter()


@router.get("/sources", response_class=HTMLResponse)
def sources_page(request: Request, db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.country, Source.name).all()
    failures = (
        db.query(CrawlFailure)
        .filter(CrawlFailure.resolved_at.is_(None))
        .all()
    )
    failure_map = {}
    for failure in failures:
        failure_map.setdefault(failure.source_id, []).append(failure)
    return templates.TemplateResponse(
        request,
        "sources.html",
        {
            "request": request,
            "sources": sources,
            "failure_map": failure_map,
            **build_sidebar_context(db),
        },
    )


@router.post("/sources/{source_id}/toggle")
def toggle_source(source_id: int, db: Session = Depends(get_db)):
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
def retry_source(source_id: int, db: Session = Depends(get_db)):
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
