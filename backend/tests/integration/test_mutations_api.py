"""Behavior contracts for the inventory-mutation endpoints.

Covers lot listing, manual lot edit, manual consumption (FEFO reduce),
discard, and the cooking preview/commit deduction gate.
"""

from pathlib import Path

from app.config import get_settings
from app.infrastructure.db.models import ActivityEventRow, InventoryTransactionRow
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def make_client(tmp_path: Path, monkeypatch, name: str = "mutations.db") -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / name}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


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
        if item["foodKey"] == food and item["location"] == location:
            return item["quantity"]
    return None


def test_lots_listing_returns_fefo_order(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    later = check_in(client, "lot-later", expires_on="2026-07-25", quantity="100")
    earlier = check_in(client, "lot-earlier", expires_on="2026-07-19", quantity="250")
    check_in(client, "lot-other-location", location="PANTRY")
    check_in(client, "lot-other-food", food="tofu", unit="piece")

    response = client.get("/api/inventory/lots?foodKey=spinach&location=FRIDGE")
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
    lot_id = check_in(client, "patch-lot", quantity="250")

    edited = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-1", "quantity": "200"},
    )
    assert edited.status_code == 200
    assert edited.json() == {"lotId": lot_id, "replayed": False}
    assert storage_quantity(client, "spinach", "FRIDGE") == "200"

    moved = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-2", "location": "FREEZER"},
    )
    assert moved.status_code == 200
    assert storage_quantity(client, "spinach", "FRIDGE") is None
    assert storage_quantity(client, "spinach", "FREEZER") == "200"

    replay = client.patch(
        f"/api/lots/{lot_id}",
        json={"idempotencyKey": "patch-1", "quantity": "200"},
    )
    assert replay.status_code == 200
    assert replay.json() == {"lotId": lot_id, "replayed": True}
    # No double application and no move back from the replayed edit.
    assert storage_quantity(client, "spinach", "FREEZER") == "200"

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


def test_reduce_consumes_fefo_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    earlier = check_in(client, "reduce-earlier", expires_on="2026-07-19", quantity="100")
    later = check_in(client, "reduce-later", expires_on="2026-07-25", quantity="300")

    reduced = client.post(
        "/api/inventory/reduce",
        json={
            "idempotencyKey": "reduce-1",
            "foodKey": "spinach",
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
    assert storage_quantity(client, "spinach", "FRIDGE") == "250"

    lots = client.get("/api/inventory/lots?foodKey=spinach&location=FRIDGE").json()["lots"]
    by_id = {lot["lotId"]: lot for lot in lots}
    assert by_id[earlier]["status"] == "DEPLETED"
    assert by_id[earlier]["quantity"] == "0"
    assert by_id[later]["quantity"] == "250"

    replay = client.post(
        "/api/inventory/reduce",
        json={
            "idempotencyKey": "reduce-1",
            "foodKey": "spinach",
            "location": "FRIDGE",
            "amount": "150",
            "unit": "g",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["newQuantity"] == "250"
    assert storage_quantity(client, "spinach", "FRIDGE") == "250"

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
            "foodKey": "spinach",
            "location": "FRIDGE",
            "amount": "9999",
            "unit": "g",
        },
    )
    assert insufficient.status_code == 409
    assert "insufficient quantity" in insufficient.json()["detail"]
    assert storage_quantity(client, "spinach", "FRIDGE") == "250"
    get_settings.cache_clear()


def test_discard_lot(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)
    keep = check_in(client, "discard-keep", quantity="100")
    gone = check_in(client, "discard-gone", quantity="150", expires_on="2026-07-25")

    discarded = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-1"})
    assert discarded.status_code == 200
    assert discarded.json() == {"lotId": gone, "replayed": False}
    assert storage_quantity(client, "spinach", "FRIDGE") == "100"

    replay = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-1"})
    assert replay.status_code == 200
    assert replay.json() == {"lotId": gone, "replayed": True}

    again = client.post(f"/api/lots/{gone}/discard", json={"idempotencyKey": "discard-2"})
    assert again.status_code == 409

    missing = client.post("/api/lots/no-such-lot/discard", json={"idempotencyKey": "discard-3"})
    assert missing.status_code == 404

    lots = client.get("/api/inventory/lots?foodKey=spinach&location=FRIDGE").json()["lots"]
    assert [lot["lotId"] for lot in lots] == [keep]
    get_settings.cache_clear()


def test_cooking_preview_reports_shortfall_and_persists_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    client = make_client(tmp_path, monkeypatch)
    lot_id = check_in(client, "preview-lot", quantity="300")

    preview = client.post(
        "/api/cooking/preview",
        json={
            "items": [
                {"foodKey": "spinach", "amount": "300", "unit": "g"},
                {"foodKey": "tofu", "amount": "2", "unit": "piece"},
            ]
        },
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["feasible"] is False
    spinach_line = next(line for line in body["lines"] if line["foodKey"] == "spinach")
    assert spinach_line["requested"] == "300"
    assert spinach_line["allocated"] == "300"
    assert spinach_line["shortfall"] == "0"
    assert spinach_line["allocations"] == [
        {"lotId": lot_id, "quantity": "300", "lotQuantity": "300"}
    ]
    tofu_line = next(line for line in body["lines"] if line["foodKey"] == "tofu")
    assert tofu_line["allocated"] == "0"
    assert tofu_line["shortfall"] == "2"
    assert tofu_line["allocations"] == []

    # Preview is a pure read: storage stays untouched.
    assert storage_quantity(client, "spinach", "FRIDGE") == "300"
    engine = client.app.state.database_engine
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(InventoryTransactionRow)) == 0
    get_settings.cache_clear()


def test_cooking_commit_is_atomic_stale_checked_and_idempotent(
    tmp_path: Path, monkeypatch
) -> None:
    client = make_client(tmp_path, monkeypatch)
    spinach_lot = check_in(client, "commit-spinach", quantity="500")
    tofu_lot = check_in(client, "commit-tofu", food="tofu", unit="piece", quantity="4")

    lines = [
        {"foodKey": "spinach", "allocations": [
            {"lotId": spinach_lot, "quantity": "200", "lotQuantity": "500"}
        ]},
        {"foodKey": "tofu", "allocations": [
            {"lotId": tofu_lot, "quantity": "1", "lotQuantity": "4"}
        ]},
    ]

    stale = client.post(
        "/api/cooking/commit",
        json={
            "idempotencyKey": "commit-stale",
            "lines": [
                {"foodKey": "spinach", "allocations": [
                    {"lotId": spinach_lot, "quantity": "200", "lotQuantity": "500"}
                ]},
                {"foodKey": "tofu", "allocations": [
                    {"lotId": tofu_lot, "quantity": "1", "lotQuantity": "3"}
                ]},
            ],
        },
    )
    assert stale.status_code == 409
    assert stale.json()["detail"] == "stale preview"
    # Rollback is total: not even the valid spinach line was applied.
    assert storage_quantity(client, "spinach", "FRIDGE") == "500"
    assert storage_quantity(client, "tofu", "FRIDGE") == "4"

    committed = client.post(
        "/api/cooking/commit",
        json={"idempotencyKey": "commit-1", "sessionName": "Dinner", "lines": lines},
    )
    assert committed.status_code == 201
    body = committed.json()
    assert body["replayed"] is False
    session_id = body["sessionId"]
    assert storage_quantity(client, "spinach", "FRIDGE") == "300"
    assert storage_quantity(client, "tofu", "FRIDGE") == "3"

    replay = client.post(
        "/api/cooking/commit",
        json={"idempotencyKey": "commit-1", "sessionName": "Dinner", "lines": lines},
    )
    assert replay.status_code == 200
    assert replay.json() == {"sessionId": session_id, "replayed": True}
    assert storage_quantity(client, "spinach", "FRIDGE") == "300"

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
