"""Contract tests for the history API."""

import uuid
from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def _fresh_client(monkeypatch, tmp_path) -> TestClient:
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())
    r = client.post("/api/auth/register", json={"username": "tester", "password": "password123"})
    assert r.status_code == 201
    return client


def test_history_lists_events_after_check_in(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    check_in = client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-1",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )
    assert check_in.status_code == 201

    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data

    check_in_event = next(
        (e for e in data["events"] if e["eventType"] == "CHECK_IN" and e["foodKey"] == "spinach"),
        None,
    )
    assert check_in_event is not None
    assert check_in_event["reversible"] is True

    get_settings.cache_clear()


def test_history_lists_events_after_cooking(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-spinach",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )
    client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-tofu",
            "foodKey": "tofu",
            "names": {"en": "Tofu"},
            "quantity": "150",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )

    preview = client.post(
        "/api/cooking/preview",
        json={
            "items": [{"foodKey": "spinach", "amount": "50", "unit": "g"}],
            "location": "FRIDGE",
        },
    )
    assert preview.status_code == 200
    preview_data = preview.json()
    assert preview_data["feasible"] is True
    allocation = preview_data["lines"][0]["allocations"][0]

    commit = client.post(
        "/api/cooking/commit",
        json={
            "idempotencyKey": "cook-1",
            "sessionName": "Test meal",
            "lines": [
                {
                    "foodKey": "spinach",
                    "allocations": [
                        {
                            "lotId": allocation["lotId"],
                            "quantity": allocation["quantity"],
                            "lotQuantity": allocation["lotQuantity"],
                        }
                    ],
                }
            ],
        },
    )
    assert commit.status_code == 201

    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    cooking_events = [e for e in data["events"] if e["eventType"] == "COOKING"]
    assert len(cooking_events) == 1
    assert cooking_events[0]["reversible"] is True

    get_settings.cache_clear()


def test_undo_cooking_restores_inventory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    check_in = client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-spinach",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )
    assert check_in.status_code == 201

    storage_before = client.get("/api/storage")
    spinach_before = next(
        item["quantity"]
        for item in storage_before.json()["inventory"]
        if item["foodKey"] == "spinach"
    )

    preview = client.post(
        "/api/cooking/preview",
        json={
            "items": [{"foodKey": "spinach", "amount": "50", "unit": "g"}],
            "location": "FRIDGE",
        },
    )
    preview_data = preview.json()
    allocation = preview_data["lines"][0]["allocations"][0]

    commit = client.post(
        "/api/cooking/commit",
        json={
            "idempotencyKey": "cook-undo-test",
            "sessionName": "Test meal",
            "lines": [
                {
                    "foodKey": "spinach",
                    "allocations": [
                        {
                            "lotId": allocation["lotId"],
                            "quantity": allocation["quantity"],
                            "lotQuantity": allocation["lotQuantity"],
                        }
                    ],
                }
            ],
        },
    )
    assert commit.status_code == 201

    history = client.get("/api/history")
    cooking_event = next(e for e in history.json()["events"] if e["eventType"] == "COOKING")

    undo_response = client.post(
        f"/api/history/{cooking_event['id']}/undo",
        json={"idempotencyKey": "undo-1"},
    )
    assert undo_response.status_code == 200
    undo_data = undo_response.json()
    assert undo_data["reversedTransactions"] >= 1
    assert undo_data["replayed"] is False

    storage_after = client.get("/api/storage")
    spinach_after = next(
        item["quantity"]
        for item in storage_after.json()["inventory"]
        if item["foodKey"] == "spinach"
    )
    assert spinach_after == spinach_before

    get_settings.cache_clear()


def test_undo_is_idempotent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-spinach",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )

    preview = client.post(
        "/api/cooking/preview",
        json={
            "items": [{"foodKey": "spinach", "amount": "50", "unit": "g"}],
            "location": "FRIDGE",
        },
    )
    preview_data = preview.json()
    allocation = preview_data["lines"][0]["allocations"][0]

    commit = client.post(
        "/api/cooking/commit",
        json={
            "idempotencyKey": "cook-idempotent",
            "sessionName": "Test meal",
            "lines": [
                {
                    "foodKey": "spinach",
                    "allocations": [
                        {
                            "lotId": allocation["lotId"],
                            "quantity": allocation["quantity"],
                            "lotQuantity": allocation["lotQuantity"],
                        }
                    ],
                }
            ],
        },
    )
    assert commit.status_code == 201

    history = client.get("/api/history")
    cooking_event = next(e for e in history.json()["events"] if e["eventType"] == "COOKING")

    first_undo = client.post(
        f"/api/history/{cooking_event['id']}/undo",
        json={"idempotencyKey": "undo-idempotent"},
    )
    assert first_undo.status_code == 200
    assert first_undo.json()["replayed"] is False

    second_undo = client.post(
        f"/api/history/{cooking_event['id']}/undo",
        json={"idempotencyKey": "undo-idempotent"},
    )
    assert second_undo.status_code == 200
    assert second_undo.json()["replayed"] is True

    get_settings.cache_clear()


def test_undo_unknown_event_returns_404(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/history/nonexistent-event-id/undo",
        json={"idempotencyKey": "undo-unknown"},
    )
    assert response.status_code == 404

    get_settings.cache_clear()


def test_undo_rejects_non_reversible_event_type(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    check_in = client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-spinach",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )
    assert check_in.status_code == 201
    lot_id = check_in.json()["lotId"]

    edit = client.patch(
        f"/api/lots/{lot_id}",
        json={
            "idempotencyKey": "edit-lot",
            "quantity": "150",
        },
    )
    assert edit.status_code == 200

    history = client.get("/api/history")
    edit_event = next(e for e in history.json()["events"] if e["eventType"] == "EDIT")

    undo = client.post(
        f"/api/history/{edit_event['id']}/undo",
        json={"idempotencyKey": "undo-edit"},
    )
    assert undo.status_code == 409

    get_settings.cache_clear()


def test_undo_discard_restores_lot(
    tmp_path: Path,
    monkeypatch,
) -> None:
    client = _fresh_client(monkeypatch, tmp_path)

    check_in = client.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "check-in-spinach",
            "foodKey": "spinach",
            "names": {"en": "Spinach"},
            "quantity": "200",
            "unit": "g",
            "location": "FRIDGE",
            "storedOn": "2026-07-20",
            "expirySource": "USER_OVERRIDE",
        },
    )
    assert check_in.status_code == 201
    lot_id = check_in.json()["lotId"]

    discard = client.post(
        f"/api/lots/{lot_id}/discard",
        json={
            "idempotencyKey": "discard-lot",
        },
    )
    assert discard.status_code == 200

    history = client.get("/api/history")
    discard_event = next(e for e in history.json()["events"] if e["eventType"] == "DISCARD")

    undo = client.post(
        f"/api/history/{discard_event['id']}/undo",
        json={"idempotencyKey": "undo-discard"},
    )
    assert undo.status_code == 200
    assert undo.json()["replayed"] is False

    lots_after_undo = client.get("/api/inventory/lots?foodKey=spinach&location=FRIDGE")
    # Find the user's lot (has expires_on=None from USER_OVERRIDE)
    lot = next(lot for lot in lots_after_undo.json()["lots"] if lot["expiresOn"] is None)
    assert lot["status"] == "ACTIVE"
    assert lot["quantity"] == "200"

    get_settings.cache_clear()
