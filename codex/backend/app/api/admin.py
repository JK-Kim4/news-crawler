from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.admin import AdminOverviewResponse, CrawlTriggerRequest, CrawlTriggerResponse
from app.schemas.source import SourceResponse, SourceUpdateRequest
from app.services.content import admin_overview
from app.services.source_config import sync_sources
from app.tasks.crawl import trigger_manual_crawl
from app.models.source import Source


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(db: Session = Depends(get_db)) -> AdminOverviewResponse:
    return AdminOverviewResponse(**admin_overview(db))


@router.post("/crawl/run", response_model=CrawlTriggerResponse)
def run_crawl(payload: CrawlTriggerRequest, db: Session = Depends(get_db)) -> CrawlTriggerResponse:
    sync_sources(db)
    task = trigger_manual_crawl.delay(payload.source_ids or [], "manual")
    return CrawlTriggerResponse(status="queued", task_id=str(task.id))


@router.get("/sources", response_model=list[SourceResponse])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return db.query(Source).order_by(Source.language.asc(), Source.name.asc()).all()


@router.put("/sources/{source_id}", response_model=SourceResponse)
def update_source(source_id: str, payload: SourceUpdateRequest, db: Session = Depends(get_db)) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source

