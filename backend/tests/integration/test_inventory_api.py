"""Minimal vertical contract for check-in and the Storage overview."""

import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.config import get_settings
from app.infrastructure.db.models import FoodDefinitionRow, InventoryLotRow
from app.infrastructure.db.session import create_database
from app.main import create_app
from fastapi.testclient import TestClient


def _fresh_client(tmp_path: Path, monkeypatch, username: str = "tester") -> TestClient:
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())
    # Register a test user — this sets the fp_session cookie
    r = client.post("/api/auth/register", json={"username": username, "password": "password123"})
    assert r.status_code == 201, r.text
    return client


def test_check_in_is_idempotent_and_storage_aggregates_lots(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(tmp_path, monkeypatch)

    # Use a food not in demo seed to avoid interference
    first_payload = {
        "idempotencyKey": "check-in-kale-1",
        "foodKey": "kale",
        "names": {"en": "Kale", "zh-CN": "羽衣甘蓝"},
        "quantity": "250",
        "unit": "g",
        "location": "FRIDGE",
        "storedOn": "2026-07-18",
        "expiresOn": "2026-07-18",
        "expirySource": "LIBRARY_DEFAULT",
    }
    second_payload = {
        **first_payload,
        "idempotencyKey": "check-in-kale-2",
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
    # Filter to only kale items to avoid demo data interference
    kale_items = [i for i in storage.json()["inventory"] if i["foodKey"] == "kale"]
    assert kale_items == [
        {
            "foodKey": "kale",
            "names": {"en": "Kale", "zh-CN": "羽衣甘蓝"},
            "visualKey": "kale",
            "customIcon": None,
            "quantity": "350",
            "unit": "g",
            "location": "FRIDGE",
            "urgency": "TODAY",
        }
    ]
    get_settings.cache_clear()


def test_demo_seed_is_idempotent_and_makes_storage_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "demo.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "true")
    get_settings.cache_clear()

    # A new user gets demo data cloned at registration
    first_client = TestClient(create_app())
    demo_register = first_client.post(
        "/api/auth/register",
        json={"username": "demo_tester", "password": "password123"},
    )
    assert demo_register.status_code == 201, demo_register.text
    # Seeds are stamped with the current date, so the view must use the same day.
    seed_day = date.today().isoformat()
    first_storage = first_client.get(f"/api/storage?today={seed_day}")
    assert first_storage.status_code == 200
    # Demo data has 16 items; verify inventory is non-empty
    assert len(first_storage.json()["inventory"]) >= 15
    assert len(first_storage.json()["useSoon"]) >= 5

    # Registering the same user again returns 409
    second_client = TestClient(create_app())
    r2 = second_client.post(
        "/api/auth/register",
        json={"username": "demo_tester", "password": "password123"},
    )
    assert r2.status_code == 409

    # A new user gets their own demo data clone
    third_client = TestClient(create_app())
    r3 = third_client.post(
        "/api/auth/register",
        json={"username": "newbie", "password": "password123"},
    )
    assert r3.status_code == 201
    third_storage = third_client.get(f"/api/storage?today={seed_day}")
    assert third_storage.status_code == 200
    assert len(third_storage.json()["inventory"]) >= 15
    get_settings.cache_clear()


def test_startup_normalizes_legacy_count_aliases_idempotently(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from app.auth.service import create_user

    database_path = tmp_path / "legacy-units.db"
    database_url = f"sqlite:///{database_path}"
    _, factory = create_database(database_url)

    # Create a user directly so we can use its user_id for the legacy lots
    with factory() as session:
        user = create_user(session, "legacy", "password123")
        aliases = ("head", "bulb", "clove", "bunch")
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
                    user_id=user.id,
                )
            )
        session.commit()

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()

    client = TestClient(create_app())
    # Login as the legacy user to get the cookie
    login = client.post("/api/auth/login", json={"username": "legacy", "password": "password123"})
    assert login.status_code == 200, login.text

    first = client.get("/api/storage?today=2026-07-18")
    second = client.get("/api/storage?today=2026-07-18")

    assert first.status_code == 200
    assert {item["unit"] for item in first.json()["inventory"]} == {"piece"}
    quantities = {item["foodKey"]: item["quantity"] for item in first.json()["inventory"]}
    assert quantities == {
        "legacy-head": "1",
        "legacy-bulb": "2",
        "legacy-clove": "3",
        "legacy-bunch": "4",
    }
    assert second.json() == first.json()
    get_settings.cache_clear()
