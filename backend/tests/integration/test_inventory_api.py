"""Minimal vertical contract for check-in and the Storage overview."""

from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_check_in_is_idempotent_and_storage_aggregates_lots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "inventory.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    first_payload = {
        "idempotencyKey": "check-in-spinach-1",
        "foodKey": "spinach",
        "names": {"en": "Spinach", "zh-CN": "菠菜"},
        "quantity": "250",
        "unit": "g",
        "location": "FRIDGE",
        "storedOn": "2026-07-18",
        "expiresOn": "2026-07-18",
        "expirySource": "LIBRARY_DEFAULT",
    }
    second_payload = {
        **first_payload,
        "idempotencyKey": "check-in-spinach-2",
        "quantity": "100",
        "expiresOn": "2026-07-23",
    }

    first = client.post("/api/inventory/check-in", json=first_payload)
    replay = client.post("/api/inventory/check-in", json=first_payload)
    second = client.post("/api/inventory/check-in", json=second_payload)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["lotId"] == first.json()["lotId"]
    assert replay.json()["replayed"] is True
    assert second.status_code == 201

    storage = client.get("/api/storage?today=2026-07-18")
    assert storage.status_code == 200
    assert storage.json()["inventory"] == [
        {
            "foodKey": "spinach",
            "names": {"en": "Spinach", "zh-CN": "菠菜"},
            "visualKey": "spinach",
            "quantity": "350",
            "unit": "g",
            "location": "FRIDGE",
            "urgency": "TODAY",
        }
    ]
    assert storage.json()["useSoon"] == storage.json()["inventory"]
    get_settings.cache_clear()


def test_demo_seed_is_idempotent_and_makes_storage_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "demo.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "true")
    get_settings.cache_clear()

    first_client = TestClient(create_app())
    first_storage = first_client.get("/api/storage?today=2026-07-18")
    assert first_storage.status_code == 200
    assert len(first_storage.json()["inventory"]) == 16
    assert len(first_storage.json()["useSoon"]) == 7

    second_client = TestClient(create_app())
    second_storage = second_client.get("/api/storage?today=2026-07-18")
    assert second_storage.json() == first_storage.json()
    get_settings.cache_clear()
