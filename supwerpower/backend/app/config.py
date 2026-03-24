from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./news_crawler.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ANTHROPIC_API_KEY: str = ""
    CORS_ORIGINS: str = "*"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    CRAWL_INTERVAL_HOURS: int = 6

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
