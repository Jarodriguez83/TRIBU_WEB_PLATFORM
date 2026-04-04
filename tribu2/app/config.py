from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Tribu"
    app_env: str = "development"
    base_url: str = "http://localhost:8000"

    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    wompi_public_key: Optional[str] = None
    wompi_private_key: Optional[str] = None
    wompi_events_secret: Optional[str] = None
    wompi_env: str = "sandbox"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
