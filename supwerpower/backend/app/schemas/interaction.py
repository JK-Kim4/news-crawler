from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.content import ContentResponse


class BookmarkCreate(BaseModel):
    content_id: str


class BookmarkResponse(BaseModel):
    id: str
    user_id: str
    content_id: str
    created_at: datetime
    content: ContentResponse | None = None

    model_config = {"from_attributes": True}


class BookmarkListResponse(BaseModel):
    items: list[BookmarkResponse]
    total: int


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: str
    user_id: str
    content_id: str
    text: str
    created_at: datetime
    updated_at: datetime
    username: str | None = None

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int
