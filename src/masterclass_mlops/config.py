from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "gateway"
    database_url: str = "sqlite:///./data/masterclass.db"
    model_service_url: str = "http://localhost:8001"
    session_ttl_minutes: int = 90
    password_salt: str = "masterclass-demo-salt"
    inference_delay_seconds: float = 0.0
    public_api_url: str = "http://localhost:8080"
    log_file_path: str = ""
    otel_exporter_endpoint: str = ""
    service_version: str = "0.1.0"
    model_version: str = "keyword-v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
