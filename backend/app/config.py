"""Application settings loaded from environment variables."""

import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the Fridge Pal application service."""

    model_config = SettingsConfigDict(env_file=str(_PROJECT_ROOT / ".env"), extra="ignore")

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
    # Fixed admin account provisioned at startup (username/password from env).
    admin_username: str = Field(default="admin", alias="FRIDGE_PAL_ADMIN_USERNAME")
    admin_password: str = Field(default="", alias="FRIDGE_PAL_ADMIN_PASSWORD")
    cookie_secure: bool = Field(default=False, alias="FRIDGE_PAL_COOKIE_SECURE")
    # Auth brute-force protection; requests per minute per client address, 0 disables.
    auth_login_rate_per_minute: int = Field(default=10, alias="AUTH_LOGIN_RATE_PER_MINUTE")
    auth_register_rate_per_minute: int = Field(default=5, alias="AUTH_REGISTER_RATE_PER_MINUTE")


def validate_auth_settings(settings: Settings) -> list[str]:
    """Return human-readable problems with the auth configuration (empty when valid).

    A misconfigured deployment must fail fast at startup instead of booting into
    broken token signing (empty JWT secret) or a crash while creating the demo
    account (empty demo password).
    """
    problems: list[str] = []
    if not settings.jwt_secret:
        problems.append("FRIDGE_PAL_JWT_SECRET must be set (generate with: openssl rand -hex 32)")
    elif len(settings.jwt_secret) < 32:
        problems.append("FRIDGE_PAL_JWT_SECRET must be at least 32 characters")
    if not settings.demo_password:
        problems.append("FRIDGE_PAL_DEMO_PASSWORD must be set")
    elif len(settings.demo_password) < 8:
        problems.append("FRIDGE_PAL_DEMO_PASSWORD must be at least 8 characters")
    if not settings.admin_password:
        problems.append("FRIDGE_PAL_ADMIN_PASSWORD must be set")
    elif len(settings.admin_password) < 8:
        problems.append("FRIDGE_PAL_ADMIN_PASSWORD must be at least 8 characters")
    if settings.admin_username and not re.fullmatch(r"[a-zA-Z0-9_-]+", settings.admin_username):
        problems.append(
            "FRIDGE_PAL_ADMIN_USERNAME may only contain letters, numbers, underscores, and hyphens"
        )
    return problems


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
