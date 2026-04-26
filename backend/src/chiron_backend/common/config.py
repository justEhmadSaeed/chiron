from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_port: int = 8000
    # Comma-separated origins. Wildcard "*" is invalid with allow_credentials=True in browsers.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,https://chiron-web-eta.vercel.app"
    )
    redis_url: str = "redis://localhost:6379/0"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    firebase_credentials_path: str | None = None
    firebase_service_account_json: str | None = None
    firebase_database_url: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
