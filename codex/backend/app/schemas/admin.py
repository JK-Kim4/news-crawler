from datetime import datetime

from pydantic import BaseModel


class CrawlTriggerRequest(BaseModel):
    source_ids: list[str] | None = None


class CrawlTriggerResponse(BaseModel):
    status: str
    task_id: str


class AdminOverviewResponse(BaseModel):
    total_users: int
    total_contents: int
    total_sources: int
    active_sources: int
    last_crawl_status: str | None
    last_crawl_at: datetime | None

