from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"
DEFAULT_SOURCES_PATH = ROOT_DIR / "sources.json"


class Settings(BaseSettings):
    app_name: str = "AI Insights Service"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./news_crawler.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "development-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    summary_provider: str = "mock"
    openai_api_key: str = ""
    frontend_origin: str = "http://localhost:3000"
    sources_path: Path = DEFAULT_SOURCES_PATH

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_prefix="AINSIGHTS_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

