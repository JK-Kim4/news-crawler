from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class SourceType(str, Enum):
    PAPER = "PAPER"
    BLOG = "BLOG"
    NEWS = "NEWS"


class CrawlStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

