from datetime import datetime

from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: str
    key: str
    name: str
    base_url: str
    rss_url: str | None
    selector_title: str
    selector_content: str
    language: str
    source_type: str
    is_active: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceUpdateRequest(BaseModel):
    name: str | None = None
    rss_url: str | None = None
    selector_title: str | None = None
    selector_content: str | None = None
    language: str | None = None
    is_active: bool | None = None

