import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.models.content import Content
from app.schemas.content import ContentDetailResponse, ContentListResponse, ContentResponse

router = APIRouter(prefix="/contents", tags=["contents"])


@router.get("/search", response_model=ContentListResponse)
async def search_contents(
    q: str = Query(..., min_length=1, description="Search keyword"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    search_term = f"%{q}%"

    where_clause = or_(
        Content.title.ilike(search_term),
        Content.summary.ilike(search_term),
    )

    count_query = select(func.count()).select_from(Content).where(where_clause)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(Content)
        .where(where_clause)
        .order_by(Content.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return ContentListResponse(
        items=[ContentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get("/", response_model=ContentListResponse)
async def list_contents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    source_type: str | None = Query(None, description="Filter by source type: PAPER, BLOG, NEWS"),
    source_name: str | None = Query(None, description="Filter by source name"),
    tag: str | None = Query(None, description="Filter by tag"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Content)
    count_query = select(func.count()).select_from(Content)

    if source_type:
        query = query.where(Content.source_type == source_type)
        count_query = count_query.where(Content.source_type == source_type)

    if source_name:
        query = query.where(Content.source_name == source_name)
        count_query = count_query.where(Content.source_name == source_name)

    if tag:
        query = query.where(Content.tags.contains(tag))
        count_query = count_query.where(Content.tags.contains(tag))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Content.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return ContentListResponse(
        items=[ContentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get("/{content_id}", response_model=ContentDetailResponse)
async def get_content(content_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )

    return ContentDetailResponse.model_validate(content)
