"""Startup configuration validation for the auth and admin boundary."""

from app.config import Settings, validate_auth_settings


def _valid_env(monkeypatch) -> None:
    monkeypatch.setenv("FRIDGE_PAL_JWT_SECRET", "x" * 40)
    monkeypatch.setenv("FRIDGE_PAL_DEMO_PASSWORD", "demo-pass-123")
    monkeypatch.setenv("FRIDGE_PAL_ADMIN_PASSWORD", "admin-pass-123")


def test_valid_auth_configuration_passes(monkeypatch) -> None:
    _valid_env(monkeypatch)
    settings = Settings()
    assert validate_auth_settings(settings) == []


def test_missing_secret_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_JWT_SECRET", "")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("FRIDGE_PAL_JWT_SECRET" in problem for problem in problems)


def test_short_secret_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_JWT_SECRET", "too-short")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("32 characters" in problem for problem in problems)


def test_missing_demo_password_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_DEMO_PASSWORD", "")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("FRIDGE_PAL_DEMO_PASSWORD" in problem for problem in problems)


def test_short_demo_password_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_DEMO_PASSWORD", "short")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("8 characters" in problem for problem in problems)


def test_missing_admin_password_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_ADMIN_PASSWORD", "")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("FRIDGE_PAL_ADMIN_PASSWORD" in problem for problem in problems)


def test_short_admin_password_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_ADMIN_PASSWORD", "short")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("8 characters" in problem for problem in problems)


def test_invalid_admin_username_is_reported(monkeypatch) -> None:
    _valid_env(monkeypatch)
    monkeypatch.setenv("FRIDGE_PAL_ADMIN_USERNAME", "bad name!")
    settings = Settings()
    problems = validate_auth_settings(settings)
    assert any("FRIDGE_PAL_ADMIN_USERNAME" in problem for problem in problems)


def test_admin_username_defaults_to_admin(monkeypatch) -> None:
    _valid_env(monkeypatch)
    settings = Settings()
    assert settings.admin_username == "admin"
