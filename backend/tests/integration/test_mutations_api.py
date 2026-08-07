"""Behavior contracts for the inventory-mutation endpoints.

Covers lot listing, manual lot edit, manual consumption (FEFO reduce),
discard, and the cooking preview/commit deduction gate.
"""

import uuid
from pathlib import Path

from app.config import get_settings
from app.infrastructure.db.models import ActivityEventRow, InventoryTransactionRow
from app.main import create_app
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def make_client(tmp_path: Path, monkeypatch, name: str = "mutations.db") -> TestClient:
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())
    # Register a test user — this sets the fp_session cookie
    r = client.post("/api/auth/register", json={"username": "tester", "password": "password123"})
    assert r.status_code == 201, r.text
    return client


def check_in(
    client: TestClient,
    key: str,
    food: str = "spinach",
    quantity: str = "250",
    unit: str = "g",
    location: str = "FRIDGE",
    expires_on: str | None = "2026-07-20",
) -> str:
    response = client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": key,
            "foodKey": food,
            "names": {"en": food.title()},
            "quantity": quantity,
            "unit": unit,
            "location": location,
            "storedOn": "2026-07-18",
            "expiresOn": expires_on,
            "expirySource": "LIBRARY_DEFAULT",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["lotId"]


def storage_quantity(client: TestClient, food: str, location: str) -> str | None:
    storage = client.get("/api/storage?today=2026-07-18")
    assert storage.status_code == 200
    for item in storage.json()["inventory"]:
        if (
            item["foodKey"] == food or item["visualKey"] == food
        ) and item["location"] == location:
            return item["quantity"]
    return None


def post_check_in(
    client: TestClient,
    key: str,
    *,
    food: str,
    quantity: str,
    unit: str,
) -> Response:
    return client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": key,
            "foodKey": food,
            "names": {"en": food.title()},
            "quantity": quantity,
            "unit": unit,
            "location": "FRIDGE",
            "storedOn": "2026-07-18",
            "expiresOn": None,
            "expirySource": "NONE",
        },
    )


def test_check_in_converts_compatible_mass_and_volume_units(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    cases = (
        ("mass-to-g", "100", "g", "0.5", "kg", "600", "g"),
        ("mass-to-kg", "2", "kg", "500", "g", "2.5", "kg"),
        ("volume-to-ml", "250", "ml", "1.5", "l", "1750", "ml"),
        ("volume-to-l", "2", "l", "500", "ml", "2.5", "l"),
    )

    for food, first_quantity, first_unit, second_quantity, second_unit, total, base_unit in cases:
        check_in(
            client,
            f"{food}-first",
            food=food,
            quantity=first_quantity,
            unit=first_unit,
            expires_on=None,
        )
        response = post_check_in(
            client,
            f"{food}-second",
            food=food,
            quantity=second_quantity,
            unit=second_unit,
        )

        assert response.status_code == 201, response.text
        storage = client.get("/api/storage?today=2026-07-18").json()["inventory"]
        item = next(row for row in storage if row["visualKey"] == food)
        assert item["quantity"] == total
        assert item["unit"] == base_unit
    get_settings.cache_clear()


def test_check_in_rejects_food_specific_count_units(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)

    for unit in ("head", "bulb", "clove", "bunch"):
        response = post_check_in(
            client,
            f"reject-{unit}",
            food=f"food-{unit}",
            quantity="2",
            unit=unit,
        )
        assert response.status_code == 422
    get_settings.cache_clear()


def test_lots_listing_returns_fefo_order(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale (not in demo seed) to avoid interference
    later = check_in(client, "lot-later", food="kale", expires_on="2026-07-25", quantity="100")
    earlier = check_in(client, "lot-earlier", food="kale", expires_on="2026-07-19", quantity="250")
    check_in(client, "lot-other-location", location="PANTRY")
    check_in(client, "lot-other-food", food="chickpeas", unit="g")

    response = client.get("/api/inventory/lots?foodKey=kale&location=FRIDGE")
    assert response.status_code == 200
    lots = response.json()["lots"]
    assert [lot["lotId"] for lot in lots] == [earlier, later]
    assert lots[0] == {
        "lotId": earlier,
        "quantity": "250",
        "unit": "g",
        "location": "FRIDGE",
        "storedOn": "2026-07-18",
        "expiresOn": "2026-07-19",
        "expirySource": "LIBRARY_DEFAULT",
        "status": "ACTIVE",
    }
    get_settings.cache_clear()


def test_patch_lot_quantity_and_location(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale (not in demo seed) to avoid interference
    lot_id = check_in(client, "patch-lot", food="kale", quantity="250", unit="g")

    edited = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-1", "quantity": "200"},
    )
    assert edited.status_code == 200
    assert edited.json() == {"lotId": lot_id, "replayed": False}
    assert storage_quantity(client, "kale", "FRIDGE") == "200"

    moved = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-2", "location": "FREEZER"},
    )
    assert moved.status_code == 200
    assert storage_quantity(client, "kale", "FRIDGE") is None
    assert storage_quantity(client, "kale", "FREEZER") == "200"

    replay = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-1", "quantity": "200"},
    )
    assert replay.status_code == 200
    assert replay.json() == {"lotId": lot_id, "replayed": True}
    # No double application and no move back from the replayed edit.
    assert storage_quantity(client, "kale", "FREEZER") == "200"

    missing = client.patch(
        "/api/lots/no-such-lot",
        json={"idempotencyKey": "patch-3", "quantity": "10"},
    )
    assert missing.status_code == 404

    no_fields = client.patch(f"/api/lots/{lot_id}", json={"idempotencyKey": "patch-4"})
    assert no_fields.status_code == 422

    zero = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-5", "quantity": "0"},
    )
    assert zero.status_code == 422
    get_settings.cache_clear()


def test_patch_lot_corrects_unit_and_stored_date_in_one_audited_edit(
    tmp_path: Path, monkeypatch
) -> None:
    client = make_client(tmp_path, monkeypatch)
    lot_id = check_in(client, "patch-unit-date", food="garlic", quantity="80", unit="g")

    edited = client.patch(
        f"/api/lots/{lot_id}",
        json={
            "idempotencyKey": "patch-unit-date-1",
            "quantity": "0.08",
            "unit": "kg",
            "storedOn": "2026-07-16",
        },
    )

    assert edited.status_code == 200, edited.text
    lots = client.get("/api/inventory/lots?foodKey=garlic&location=FRIDGE").json()["lots"]
    assert lots[0]["quantity"] == "0.08"
    assert lots[0]["unit"] == "kg"
    assert lots[0]["storedOn"] == "2026-07-16"
    assert storage_quantity(client, "garlic", "FRIDGE") == "0.08"

    engine = client.app.state.database_engine
    with Session(engine) as session:
        event = session.scalar(
            select(ActivityEventRow).where(ActivityEventRow.idempotency_key == "patch-unit-date-1")
        )
        assert event is not None
        assert event.display_snapshot["changes"]["unit"] == {"from": "g", "to": "kg"}
        assert event.display_snapshot["changes"]["storedOn"] == {
            "from": "2026-07-18",
            "to": "2026-07-16",
        }

    blank_unit = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-unit-date-2", "unit": "   "},
    )
    assert blank_unit.status_code == 422
    get_settings.cache_clear()


def test_patch_base_unit_converts_every_lot_transactionally(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    first = check_in(client, "convert-lot-1", food="rice", quantity="500", unit="g")
    second = check_in(client, "convert-lot-2", food="rice", quantity="750", unit="g")

    edited = client.patch(
        f"/api/lots/{first}",
        json={"idempotencyKey": "convert-base-unit", "unit": "kg"},
    )

    assert edited.status_code == 200, edited.text
    lots = client.get("/api/inventory/lots?foodKey=rice&location=FRIDGE").json()["lots"]
    by_id = {lot["lotId"]: lot for lot in lots}
    assert by_id[first]["quantity"] == "0.5"
    assert by_id[second]["quantity"] == "0.75"
    assert {lot["unit"] for lot in lots} == {"kg"}
    assert storage_quantity(client, "rice", "FRIDGE") == "1.25"
    get_settings.cache_clear()


def test_reduce_consumes_fefo_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale (not in demo seed) to avoid interference
    earlier = check_in(
        client, "reduce-earlier", food="kale", expires_on="2026-07-19", quantity="100"
    )
    later = check_in(client, "reduce-later", food="kale", expires_on="2026-07-25", quantity="300")

    reduced = client.post(
        "/api/inventory/reduce",
        json={
            "idempotencyKey": "reduce-1",
            "foodKey": "kale",
            "location": "FRIDGE",
            "amount": "150",
            "unit": "g",
        },
    )
    assert reduced.status_code == 200
    body = reduced.json()
    assert body["replayed"] is False
    assert body["newQuantity"] == "250"
    assert body["allocations"] == [
        {"lotId": earlier, "deducted": "100"},
        {"lotId": later, "deducted": "50"},
    ]
    assert storage_quantity(client, "kale", "FRIDGE") == "250"

    lots = client.get("/api/inventory/lots?foodKey=kale&location=FRIDGE").json()["lots"]
    by_id = {lot["lotId"]: lot for lot in lots}
    assert by_id[earlier]["status"] == "DEPLETED"
    assert by_id[earlier]["quantity"] == "0"
    assert by_id[later]["quantity"] == "250"

    replay = client.post(
        "/api/inventory/reduce",
        json={
            "idempotencyKey": "reduce-1",
            "foodKey": "kale",
            "location": "FRIDGE",
            "amount": "150",
            "unit": "g",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["newQuantity"] == "250"
    assert storage_quantity(client, "kale", "FRIDGE") == "250"

    engine = client.app.state.database_engine
    with Session(engine) as session:
        transactions = session.scalars(
            select(InventoryTransactionRow).where(
                InventoryTransactionRow.reason == "MANUAL_CONSUMPTION"
            )
        ).all()
        assert len(transactions) == 2
        assert {row.lot_id for row in transactions} == {earlier, later}
        assert sum(row.quantity_delta for row in transactions) == -150
        events = session.scalars(
            select(ActivityEventRow).where(ActivityEventRow.event_type == "MANUAL_CONSUMPTION")
        ).all()
        assert len(events) == 1
        assert events[0].quantity_delta == -150

    insufficient = client.post(
        "/api/inventory/reduce",
        json={
            "idempotencyKey": "reduce-2",
            "foodKey": "kale",
            "location": "FRIDGE",
            "amount": "9999",
            "unit": "g",
        },
    )
    assert insufficient.status_code == 409
    assert "insufficient quantity" in insufficient.json()["detail"]
    assert storage_quantity(client, "kale", "FRIDGE") == "250"
    get_settings.cache_clear()


def test_discard_lot(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale (not in demo seed) to avoid interference
    keep = check_in(client, "discard-keep", food="kale", quantity="100")
    gone = check_in(client, "discard-gone", food="kale", quantity="150", expires_on="2026-07-25")

    discarded = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-1"})
    assert discarded.status_code == 200
    assert discarded.json() == {"lotId": gone, "replayed": False}
    assert storage_quantity(client, "kale", "FRIDGE") == "100"

    replay = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-1"})
    assert replay.status_code == 200
    assert replay.json() == {"lotId": gone, "replayed": True}

    again = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-2"})
    assert again.status_code == 409

    missing = client.post("/api/lots/no-such-lot/discard", json={"idempotencyKey": "discard-3"})
    assert missing.status_code == 404

    lots = client.get("/api/inventory/lots?foodKey=kale&location=FRIDGE").json()["lots"]
    assert [lot["lotId"] for lot in lots] == [keep]
    get_settings.cache_clear()


def test_cooking_preview_reports_shortfall_and_persists_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale and chickpeas (not in demo seed) to avoid interference
    lot_id = check_in(client, "preview-lot", food="kale", quantity="300")

    preview = client.post(
        "/api/cooking/preview",
        json={
            "items": [
                {"foodKey": "kale", "amount": "300", "unit": "g"},
                {"foodKey": "chickpeas", "amount": "200", "unit": "g"},
            ]
        },
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["feasible"] is False
    kale_line = next(line for line in body["lines"] if line["foodKey"] == "kale")
    assert kale_line["requested"] == "300"
    assert kale_line["allocated"] == "300"
    assert kale_line["shortfall"] == "0"
    assert kale_line["allocations"] == [{"lotId": lot_id, "quantity": "300", "lotQuantity": "300"}]
    chickpeas_line = next(line for line in body["lines"] if line["foodKey"] == "chickpeas")
    assert chickpeas_line["allocated"] == "0"
    assert chickpeas_line["shortfall"] == "200"
    assert chickpeas_line["allocations"] == []

    # Preview is a pure read: storage stays untouched.
    assert storage_quantity(client, "kale", "FRIDGE") == "300"
    engine = client.app.state.database_engine
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(InventoryTransactionRow)) == 0
    get_settings.cache_clear()


def test_cooking_commit_is_atomic_stale_checked_and_idempotent(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    # Use kale and chickpeas (not in demo seed) to avoid interference
    kale_lot = check_in(client, "commit-kale", food="kale", quantity="500")
    chickpeas_lot = check_in(client, "commit-chickpeas", food="chickpeas", unit="g", quantity="4")

    lines = [
        {
            "foodKey": "kale",
            "allocations": [{"lotId": kale_lot, "quantity": "200", "lotQuantity": "500"}],
        },
        {
            "foodKey": "chickpeas",
            "allocations": [{"lotId": chickpeas_lot, "quantity": "1", "lotQuantity": "4"}],
        },
    ]

    stale = client.post(
        "/api/cooking/commit",
        json={
            "idempotencyKey": "commit-stale",
            "lines": [
                {
                    "foodKey": "kale",
                    "allocations": [{"lotId": kale_lot, "quantity": "200", "lotQuantity": "500"}],
                },
                {
                    "foodKey": "chickpeas",
                    "allocations": [{"lotId": chickpeas_lot, "quantity": "1", "lotQuantity": "3"}],
                },
            ],
        },
    )
    assert stale.status_code == 409
    assert stale.json()["detail"] == "stale preview"
    # Rollback is total: not even the valid kale line was applied.
    assert storage_quantity(client, "kale", "FRIDGE") == "500"
    assert storage_quantity(client, "chickpeas", "FRIDGE") == "4"

    committed = client.post(
        "/api/cooking/commit",
        json={"idempotencyKey": "commit-1", "sessionName": "Dinner", "lines": lines},
    )
    assert committed.status_code == 201
    body = committed.json()
    assert body["replayed"] is False
    session_id = body["sessionId"]
    assert storage_quantity(client, "kale", "FRIDGE") == "300"
    assert storage_quantity(client, "chickpeas", "FRIDGE") == "3"

    replay = client.post(
        "/api/cooking/commit",
        json={"idempotencyKey": "commit-1", "sessionName": "Dinner", "lines": lines},
    )
    assert replay.status_code == 200
    assert replay.json() == {"sessionId": session_id, "replayed": True}
    assert storage_quantity(client, "kale", "FRIDGE") == "300"

    engine = client.app.state.database_engine
    with Session(engine) as session:
        transactions = session.scalars(
            select(InventoryTransactionRow).where(InventoryTransactionRow.reason == "COOKING")
        ).all()
        assert len(transactions) == 2
        assert {row.cooking_session_id for row in transactions} == {session_id}
        assert sum(row.quantity_delta for row in transactions) == -201
        events = session.scalars(
            select(ActivityEventRow).where(ActivityEventRow.event_type == "COOKING")
        ).all()
        assert len(events) == 1
        assert events[0].display_snapshot["sessionName"] == "Dinner"
    get_settings.cache_clear()
