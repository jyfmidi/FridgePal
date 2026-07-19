"""Production static-serving contracts for Vue history routes."""

from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_static_server_falls_back_for_client_route_but_not_missing_asset(
    tmp_path: Path,
    monkeypatch,
) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text(
        "<!doctype html><title>Fridgital SPA</title>",
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'static.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("STATIC_DIR", str(static_dir))
    get_settings.cache_clear()

    client = TestClient(create_app())

    client_route = client.get("/rescue")
    missing_asset = client.get("/assets/missing.js")

    assert client_route.status_code == 200
    assert "Fridgital SPA" in client_route.text
    assert missing_asset.status_code == 404
    get_settings.cache_clear()
