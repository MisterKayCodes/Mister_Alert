from pydantic import BaseSettings, Field, SecretStr

class Settings(BaseSettings):
    telegram_token: SecretStr = Field(..., env="TELEGRAM_TOKEN")
    database_url: str = Field("sqlite+aiosqlite:///./Mister_alert.db", env="DATABASE_URL")

    max_free_alerts: int = Field(3, env="MAX_FREE_ALERTS")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
