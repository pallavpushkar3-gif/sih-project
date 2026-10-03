from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLEET_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite+pysqlite:///./fleet.db"
    broker_url: str = "amqp://guest:guest@localhost:5672//"
    result_backend: str | None = None
    artifact_root: Path = Path("artifacts")
    session_secret: str = Field(default="local-demonstration-only", min_length=16)
    api_prefix: str = "/api"
    auto_create_schema: bool = False
    auto_seed_demo: bool = True
    outbox_poll_seconds: float = Field(default=0.5, gt=0)
    outbox_batch_size: int = Field(default=50, ge=1, le=1000)


@lru_cache
def get_settings() -> Settings:
    return Settings()
