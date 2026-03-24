import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.models.content import Content
from app.models.user import User
from app.services.crawler import get_crawl_status, run_crawl
from app.services.scheduler import get_next_run_time
from app.services.source_manager import (
    add_source,
    delete_source,
    get_all_sources,
    update_source,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class CrawlRunRequest(BaseModel):
    source_name: str | None = None


class SourceCreate(BaseModel):
    name: str
    base_url: str
    rss_url: str | None = None
    selector_title: str = "h1"
    selector_content: str = "article"
    language: str = "ko"
    source_type: str = "BLOG"
    is_active: bool = True


class SourceUpdate(BaseModel):
    base_url: str | None = None
    rss_url: str | None = None
    selector_title: str | None = None
    selector_content: str | None = None
    language: str | None = None
    source_type: str | None = None
    is_active: bool | None = None


@router.post("/crawl/run")
async def trigger_crawl(body: CrawlRunRequest | None = None):
    source_name = body.source_name if body else None

    async def _do_crawl():
        await run_crawl(source_name=source_name)

    asyncio.ensure_future(_do_crawl())

    return {
        "message": "Crawl started",
        "source_name": source_name or "all active sources",
    }


@router.get("/crawl/status")
async def crawl_status():
    status_data = get_crawl_status()
    status_data["next_scheduled_time"] = get_next_run_time()
    return status_data


@router.get("/sources")
async def list_sources():
    return get_all_sources()


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(source: SourceCreate):
    try:
        new_source = add_source(source.model_dump())
        return new_source
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/sources/{name}")
async def update_source_config(name: str, updates: SourceUpdate):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    result = update_source(name, update_data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{name}' not found",
        )

    return result


@router.delete("/sources/{name}")
async def remove_source(name: str):
    if not delete_source(name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{name}' not found",
        )
    return {"message": f"Source '{name}' deleted"}


@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_contents_result = await db.execute(select(func.count()).select_from(Content))
    total_contents = total_contents_result.scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    contents_today_result = await db.execute(
        select(func.count()).select_from(Content).where(Content.created_at >= today_start)
    )
    contents_today = contents_today_result.scalar() or 0

    total_users_result = await db.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar() or 0

    sources = get_all_sources()

    source_type_result = await db.execute(
        select(Content.source_type, func.count())
        .group_by(Content.source_type)
    )
    contents_by_type = {row[0]: row[1] for row in source_type_result.all()}

    source_name_result = await db.execute(
        select(Content.source_name, func.count())
        .group_by(Content.source_name)
    )
    contents_by_source = {row[0]: row[1] for row in source_name_result.all()}

    return {
        "total_contents": total_contents,
        "contents_today": contents_today,
        "total_users": total_users,
        "sources_count": len(sources),
        "active_sources_count": sum(1 for s in sources if s.get("is_active", True)),
        "contents_by_type": contents_by_type,
        "contents_by_source": contents_by_source,
    }
