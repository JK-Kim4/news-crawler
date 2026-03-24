from datetime import datetime

from pydantic import BaseModel


class CommentResponse(BaseModel):
    id: str
    user_id: str
    username: str
    content: str
    created_at: datetime


class CommentCreateRequest(BaseModel):
    content: str


class ContentListResponse(BaseModel):
    id: str
    source_name: str
    source_type: str
    language: str
    title: str
    original_url: str
    summary: str
    tags: list[str]
    published_at: datetime | None
    author: str | None
    bookmarked: bool = False


class ContentDetailResponse(ContentListResponse):
    raw_content: str | None
    comments: list[CommentResponse]


class NotificationPreferenceRequest(BaseModel):
    keywords: list[str]
    email_enabled: bool = False
    slack_enabled: bool = False


class NotificationPreferenceResponse(NotificationPreferenceRequest):
    id: str

