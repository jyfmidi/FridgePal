"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Fridge Pal application service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./fridgital.db"
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.io/v1"
    minimax_model: str = "MiniMax-M3"
    recipe_provider_mode: str = "fixture"
    app_timezone: str = "Asia/Shanghai"
    app_default_locale: str = "en"
    seed_demo_data: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
