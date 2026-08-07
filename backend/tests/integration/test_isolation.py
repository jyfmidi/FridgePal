from pathlib import Path

from app.config import get_settings
from app.infrastructure.db.models import FoodDefinitionRow
from app.infrastructure.db.session import create_database
from app.main import create_app
from fastapi.testclient import TestClient


def _check_in_payload(
    *,
    idempotency_key: str,
    food_key: str,
    quantity: str = "100",
    unit: str = "g",
) -> dict[str, object]:
    return {
        "idempotencyKey": idempotency_key,
        "foodKey": food_key,
        "names": {"en": "Shared family food", "zh-CN": "共享家庭食材"},
        "quantity": quantity,
        "unit": unit,
        "location": "FRIDGE",
        "storedOn": "2026-08-07",
        "expirySource": "NONE",
    }


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

    alice_foods = {item["visualKey"] for item in alice_storage.get("inventory", [])}
    bob_foods = {item["visualKey"] for item in bob_storage.get("inventory", [])}

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


def test_same_custom_food_key_creates_distinct_private_definitions_and_scoped_libraries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "personal_food_library.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    assert alice.post(
        "/api/auth/register", json={"username": "alice_personal", "password": "password123"}
    ).status_code == 201
    assert bob.post(
        "/api/auth/register", json={"username": "bob_personal", "password": "password123"}
    ).status_code == 201

    custom_key = "custom:family-noodles"
    assert alice.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="alice-personal-1", food_key=custom_key),
    ).status_code == 201
    assert bob.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="bob-personal-1", food_key=custom_key),
    ).status_code == 201

    alice_food_key = next(
        item["foodKey"]
        for item in alice.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    )
    bob_food_key = next(
        item["foodKey"]
        for item in bob.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    )
    assert alice_food_key != bob_food_key

    alice_library = {item["foodKey"] for item in alice.get("/api/library").json()}
    bob_library = {item["foodKey"] for item in bob.get("/api/library").json()}
    assert "bok-choy" in alice_library
    assert "bok-choy" in bob_library
    assert alice_food_key in alice_library
    assert alice_food_key not in bob_library
    assert bob_food_key in bob_library
    assert bob_food_key not in alice_library
    get_settings.cache_clear()


def test_same_missing_non_custom_key_creates_distinct_private_definitions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "non_custom_personal_food.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    alice.post(
        "/api/auth/register", json={"username": "alice_non_custom", "password": "password123"}
    )
    bob.post("/api/auth/register", json={"username": "bob_non_custom", "password": "password123"})

    missing_key = "temporary-local-food"
    assert alice.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="alice-non-custom-1", food_key=missing_key),
    ).status_code == 201
    assert bob.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="bob-non-custom-1", food_key=missing_key),
    ).status_code == 201

    alice_key = next(
        item["foodKey"]
        for item in alice.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    )
    bob_key = next(
        item["foodKey"]
        for item in bob.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    )
    assert alice_key != missing_key
    assert bob_key != missing_key
    assert alice_key != bob_key
    get_settings.cache_clear()


def test_existing_public_legacy_custom_key_remains_shared(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "legacy_public_custom_food.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()
    _, factory = create_database(f"sqlite:///{db_path}")
    legacy_key = "custom:legacy-shared"
    with factory() as session:
        session.add(
            FoodDefinitionRow(
                id=legacy_key,
                owner_user_id=None,
                names={"en": "Legacy shared food"},
                visual_key=legacy_key,
                base_unit="g",
                recommended_storage="FRIDGE",
            )
        )
        session.commit()

    alice = TestClient(app)
    bob = TestClient(app)
    alice.post("/api/auth/register", json={"username": "alice_legacy", "password": "password123"})
    bob.post("/api/auth/register", json={"username": "bob_legacy", "password": "password123"})
    assert alice.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="alice-legacy-1", food_key=legacy_key),
    ).status_code == 201
    assert bob.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="bob-legacy-1", food_key=legacy_key),
    ).status_code == 201

    for client in (alice, bob):
        library_keys = {item["foodKey"] for item in client.get("/api/library").json()}
        storage_keys = {item["foodKey"] for item in client.get("/api/storage").json()["inventory"]}
        assert legacy_key in library_keys
        assert legacy_key in storage_keys
    get_settings.cache_clear()


def test_check_in_rejects_foreign_personal_definition_without_writing_lot_or_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "foreign_personal_food.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    alice.post("/api/auth/register", json={"username": "alice_foreign", "password": "password123"})
    bob.post("/api/auth/register", json={"username": "bob_foreign", "password": "password123"})

    custom_key = "custom:private-peppers"
    assert alice.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="alice-foreign-1", food_key=custom_key),
    ).status_code == 201
    alice_food_key = next(
        item["foodKey"]
        for item in alice.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    )

    rejected = bob.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="bob-foreign-attack", food_key=alice_food_key),
    )
    assert rejected.status_code == 404
    assert bob.get("/api/storage").json()["inventory"] == []
    assert bob.get("/api/history").json() == {"events": []}
    get_settings.cache_clear()


def test_same_user_reuses_personal_definition_and_converts_to_its_base_unit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "personal_food_reuse.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())
    client.post(
        "/api/auth/register", json={"username": "reuse_personal", "password": "password123"}
    )

    custom_key = "custom:reuse-flour"
    assert client.post(
        "/api/inventory/check-in",
        json=_check_in_payload(
            idempotency_key="reuse-personal-1", food_key=custom_key, quantity="250"
        ),
    ).status_code == 201
    assert client.post(
        "/api/inventory/check-in",
        json=_check_in_payload(
            idempotency_key="reuse-personal-2", food_key=custom_key, quantity="1", unit="kg"
        ),
    ).status_code == 201

    personal_items = [
        item
        for item in client.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Shared family food"
    ]
    assert len(personal_items) == 1
    assert personal_items[0]["foodKey"] != custom_key
    assert personal_items[0]["quantity"] == "1250"
    assert personal_items[0]["unit"] == "g"
    get_settings.cache_clear()


def test_check_in_rejects_inactive_definition_without_writing_lot_or_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "inactive_food_definition.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    app = create_app()
    _, factory = create_database(f"sqlite:///{db_path}")
    with factory() as session:
        food = session.get(FoodDefinitionRow, "bok-choy")
        assert food is not None
        food.active = False
        session.commit()

    client = TestClient(app)
    client.post("/api/auth/register", json={"username": "inactive_food", "password": "password123"})

    rejected = client.post(
        "/api/inventory/check-in",
        json=_check_in_payload(idempotency_key="inactive-food-attack", food_key="bok-choy"),
    )
    assert rejected.status_code == 404
    assert client.get("/api/storage").json()["inventory"] == []
    assert client.get("/api/history").json() == {"events": []}
    get_settings.cache_clear()
