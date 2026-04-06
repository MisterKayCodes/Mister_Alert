from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, Union, List, Any

class Settings(BaseSettings):
    telegram_token: str = "dummy"
    database_url: str = "sqlite+aiosqlite:///./Mister_alert.db"
    max_free_alerts: int = 3
    log_level: str = "INFO"
    twelve_data_api_key: str = "your_twelve_data_key"
    polling_interval: int = 60
    admin_ids: List[int] = []
    redis_url: Optional[str] = None

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> List[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
