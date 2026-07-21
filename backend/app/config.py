"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the Fridge Pal application service."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"), extra="ignore"
    )

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
    jwt_secret: str = Field(default="", alias="FRIDGE_PAL_JWT_SECRET")
    demo_password: str = Field(default="", alias="FRIDGE_PAL_DEMO_PASSWORD")
    cookie_secure: bool = Field(default=False, alias="FRIDGE_PAL_COOKIE_SECURE")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
