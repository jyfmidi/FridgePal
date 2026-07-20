"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Fridge Pal application service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./fridgital.db"
    # Provider-neutral recipe adapters (vendors are swappable deployment config).
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    search_api_key: str = ""
    search_base_url: str = "https://api.tavily.com"
    recipe_provider_mode: str = "fixture"  # "fixture" | "live"
    app_timezone: str = "Asia/Shanghai"
    app_default_locale: str = "en"
    seed_demo_data: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
