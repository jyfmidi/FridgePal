from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_user_cannot_see_other_users_storage(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "iso_storage.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()

    alice = TestClient(app)
    alice.post("/api/auth/register", json={"username": "alice_iso", "password": "password123"})

    bob = TestClient(app)
    bob.post("/api/auth/register", json={"username": "bob_iso", "password": "password123"})

    alice.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "alice-unique-food",
            "foodKey": "alice-exclusive-food",
            "names": {"en": "Alice Exclusive"},
            "quantity": "100",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-21",
            "expirySource": "USER_OVERRIDE",
        },
    )

    bob.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "bob-unique-food",
            "foodKey": "bob-exclusive-food",
            "names": {"en": "Bob Exclusive"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-21",
            "expirySource": "USER_OVERRIDE",
        },
    )

    alice_storage = alice.get("/api/storage").json()
    bob_storage = bob.get("/api/storage").json()

    alice_foods = {item["foodKey"] for item in alice_storage.get("inventory", [])}
    bob_foods = {item["foodKey"] for item in bob_storage.get("inventory", [])}

    assert "alice-exclusive-food" in alice_foods
    assert "bob-exclusive-food" in bob_foods
    assert "alice-exclusive-food" not in bob_foods
    assert "bob-exclusive-food" not in alice_foods

    get_settings.cache_clear()


def test_user_cannot_patch_other_users_lot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "iso_patch.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()

    alice = TestClient(app)
    alice.post("/api/auth/register", json={"username": "alice_patch", "password": "password123"})

    bob = TestClient(app)
    bob.post("/api/auth/register", json={"username": "bob_patch", "password": "password123"})

    alice.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "alice-lot-test",
            "foodKey": "alice-lot-food",
            "names": {"en": "Alice Lot Food"},
            "quantity": "100",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-21",
            "expirySource": "USER_OVERRIDE",
        },
    )

    alice_lots = alice.get("/api/inventory/lots?foodKey=alice-lot-food&location=FRIDGE").json()
    alice_lot_id = alice_lots["lots"][0]["lotId"]

    r = bob.patch(
        f"/api/lots/{alice_lot_id}",
        json={"idempotencyKey": "bob-attack-1", "quantity": "999", "unit": "g"},
    )
    assert r.status_code == 404

    get_settings.cache_clear()


def test_user_cannot_discard_other_users_lot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "iso_discard.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()

    alice = TestClient(app)
    alice.post("/api/auth/register", json={"username": "alice_disc", "password": "password123"})

    bob = TestClient(app)
    bob.post("/api/auth/register", json={"username": "bob_disc", "password": "password123"})

    alice.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "alice-discard-test",
            "foodKey": "alice-discard-food",
            "names": {"en": "Alice Discard Food"},
            "quantity": "100",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-21",
            "expirySource": "USER_OVERRIDE",
        },
    )

    alice_lots = alice.get("/api/inventory/lots?foodKey=alice-discard-food&location=FRIDGE").json()
    alice_lot_id = alice_lots["lots"][0]["lotId"]

    r = bob.post(f"/api/lots/{alice_lot_id}/discard", json={"idempotencyKey": "bob-attack-2"})
    assert r.status_code == 404

    get_settings.cache_clear()


def test_unauthenticated_access_returns_401(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "iso_unauth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/api/storage").status_code == 401
    assert client.get("/api/history").status_code == 401
    assert client.get("/api/recipes").status_code == 401
    assert client.get("/api/rescue/sessions").status_code == 401

    get_settings.cache_clear()
