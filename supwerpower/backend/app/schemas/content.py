from datetime import datetime

from pydantic import BaseModel, Field


class ContentCreate(BaseModel):
    source_type: str = Field(..., max_length=20)
    source_name: str = Field(..., max_length=100)
    title: str = Field(..., max_length=500)
    original_url: str = Field(..., max_length=1000)
    published_at: datetime | None = None
    author: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    raw_content: str | None = None


class ContentResponse(BaseModel):
    id: str
    source_type: str
    source_name: str
    title: str
    original_url: str
    published_at: datetime | None = None
    author: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentDetailResponse(ContentResponse):
    raw_content: str | None = None


class ContentListResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    size: int
    pages: int
