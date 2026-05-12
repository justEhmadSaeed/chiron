from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_port: int = 8000
    # Comma-separated origins. Wildcard "*" is invalid with allow_credentials=True in browsers.
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "https://chiron-web-eta.vercel.app,"
        "https://chiron-be-heffh9eegzdcegh3.canadacentral-01.azurewebsites.net,"
        "https://chiron.ehmad.dev"
    )

    redis_url: str = "redis://localhost:6379/0"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"
    firebase_credentials_path: str | None = None
    firebase_service_account_json: str | None = None
    firebase_database_url: str | None = None
    gemini_api_key: str = ""
    groq_api_key: str = ""
    tavily_api_key: str = ""
    pinecone_api_key: str = ""
    pinecone_index_name: str = "chiron-research"
    embedding_model: str = "multilingual-e5-large"
    llm_model: str = "llama-3.3-70b-versatile"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
