from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
    )

    database_url: str = "postgresql://user:password@localhost:5432/postgres"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    openai_api_key: str = ""


settings = Settings()
