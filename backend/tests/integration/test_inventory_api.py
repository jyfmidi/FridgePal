"""Minimal vertical contract for check-in and the Storage overview."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.config import get_settings
from app.infrastructure.db.demo_seed import seed_demo_inventory
from app.infrastructure.db.models import FoodDefinitionRow, InventoryLotRow
from app.infrastructure.db.session import create_database
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
    monkeypatch.setattr(
        "app.main.seed_demo_inventory",
        lambda factory: seed_demo_inventory(factory, today=date(2026, 7, 18)),
    )
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


def test_startup_normalizes_legacy_count_aliases_idempotently(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "legacy-units.db"
    database_url = f"sqlite:///{database_path}"
    _, factory = create_database(database_url)
    aliases = ("head", "bulb", "clove", "bunch")
    with factory() as session:
        for index, alias in enumerate(aliases, start=1):
            food_key = f"legacy-{alias}"
            session.add(
                FoodDefinitionRow(
                    id=food_key,
                    names={"en": food_key},
                    visual_key=food_key,
                    base_unit=alias,
                    recommended_storage="FRIDGE",
                )
            )
            session.add(
                InventoryLotRow(
                    id=f"legacy-lot-{index}",
                    food_definition_id=food_key,
                    quantity=Decimal(index),
                    storage_location="FRIDGE",
                    stored_on=date(2026, 7, 18),
                    expires_on=None,
                    expiry_source="NONE",
                    status="ACTIVE",
                    idempotency_key=f"legacy-unit-{index}",
                )
            )
        session.commit()

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()

    first = TestClient(create_app()).get("/api/storage?today=2026-07-18")
    second = TestClient(create_app()).get("/api/storage?today=2026-07-18")

    assert first.status_code == 200
    assert {item["unit"] for item in first.json()["inventory"]} == {"piece"}
    quantities = {
        item["foodKey"]: item["quantity"] for item in first.json()["inventory"]
    }
    assert quantities == {
        "legacy-head": "1",
        "legacy-bulb": "2",
        "legacy-clove": "3",
        "legacy-bunch": "4",
    }
    assert second.json() == first.json()
    get_settings.cache_clear()
