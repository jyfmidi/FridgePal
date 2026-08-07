"""Admin console integration tests: fixed account, Food Library CRUD, settings."""

import os
import uuid

from app.main import create_app
from fastapi.testclient import TestClient

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin-pass-123"


def _client() -> TestClient:
    from app.config import get_settings

    get_settings.cache_clear()
    os.environ["DATABASE_URL"] = (
        f"sqlite:///file:test_admin_{uuid.uuid4().hex}?mode=memory&cache=shared&uri=true"
    )
    return TestClient(create_app())


def _register_user(c: TestClient, username: str = "kitchen-user") -> None:
    r = c.post("/api/auth/register", json={"username": username, "password": "password123"})
    assert r.status_code == 201


def _login_admin(c: TestClient) -> None:
    r = c.post("/api/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    assert r.json()["isAdmin"] is True


def _food_payload(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "foodKey": "avocado",
        "names": {"en": "Avocado", "zh-CN": "牛油果"},
        "aliases": {"en": ["avo"]},
        "category": "fruit",
        "visualKey": "lemon",
        "baseUnit": "piece",
        "packagePresets": [
            {"label": {"en": "Single", "zh-CN": "单个"}, "amount": "1", "unit": "piece"}
        ],
        "recommendedStorage": "FRIDGE",
        "active": True,
        "shelfLife": [{"storageLocation": "FRIDGE", "durationDays": 4}],
    }
    payload.update(overrides)
    return payload


def test_admin_account_is_provisioned_and_logs_in():
    c = _client()
    r = c.post("/api/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == ADMIN_USERNAME
    assert body["isAdmin"] is True
    assert body["isDemo"] is False


def test_admin_username_cannot_be_registered_by_regular_users():
    c = _client()
    r = c.post(
        "/api/auth/register",
        json={"username": ADMIN_USERNAME, "password": "password123"},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "AUTH_USERNAME_TAKEN"


def test_admin_endpoints_require_admin_role():
    c = _client()
    _register_user(c)
    for method, path in (
        ("GET", "/api/admin/foods"),
        ("POST", "/api/admin/foods"),
        ("GET", "/api/admin/settings"),
        ("PUT", "/api/admin/settings"),
    ):
        r = c.request(method, path, json={} if method in ("POST", "PUT") else None)
        assert r.status_code == 403, f"{method} {path} expected 403"
        assert r.json()["detail"] == "ADMIN_REQUIRED"


def test_admin_endpoints_require_authentication():
    c = _client()
    r = c.get("/api/admin/foods")
    assert r.status_code == 401


def test_admin_list_exposes_complete_seeded_food_metadata():
    c = _client()
    _login_admin(c)

    r = c.get("/api/admin/foods")
    assert r.status_code == 200
    foods = r.json()
    assert len(foods) == 72
    assert sum(food["active"] for food in foods) == 70
    assert all(
        not next(food for food in foods if food["foodKey"] == compatibility_key)["active"]
        for compatibility_key in ("rice", "pasta")
    )

    bok_choy = next(food for food in foods if food["foodKey"] == "bok-choy")
    assert bok_choy["names"] == {"en": "Bok choy", "zh-CN": "上海青"}
    assert bok_choy["category"] == "vegetable"
    assert bok_choy["aliases"] == {
        "en": ["pak choi"],
        "zh-CN": ["青菜", "小油菜"],
    }
    assert bok_choy["packagePresets"] == [
        {
            "label": {"en": "Regular amount", "zh-CN": "常用份量"},
            "amount": "300",
            "unit": "g",
        },
        {
            "label": {"en": "Large amount", "zh-CN": "大份"},
            "amount": "500",
            "unit": "g",
        },
    ]
    assert bok_choy["visualKey"] == "bok-choy"
    assert bok_choy["recommendedStorage"] == "FRIDGE"
    assert bok_choy["shelfLife"] == [
        {
            "storageLocation": "FRIDGE",
            "durationDays": 3,
            "sourceNote": (
                "Fridge Pal conservative editable starter estimate; inspect freshness and "
                "adjust in Admin."
            ),
        }
    ]


def test_create_update_and_soft_delete_food():
    c = _client()
    _login_admin(c)

    r = c.post("/api/admin/foods", json=_food_payload())
    assert r.status_code == 201
    created = r.json()
    assert created["foodKey"] == "avocado"
    assert created["origin"] == "USER_CREATED"
    assert created["shelfLife"] == [
        {"storageLocation": "FRIDGE", "durationDays": 4, "sourceNote": None}
    ]

    # Duplicate key is rejected.
    r = c.post("/api/admin/foods", json=_food_payload())
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_FOOD_EXISTS"

    # Update names, icon, category, and shelf-life rules.
    r = c.patch(
        "/api/admin/foods/avocado",
        json=_food_payload(
            names={"en": "Avocado", "zh-CN": "鳄梨"},
            visualKey="mushrooms",
            category="produce",
            shelfLife=[
                {"storageLocation": "FRIDGE", "durationDays": 6},
                {"storageLocation": "PANTRY", "durationDays": 2},
            ],
        ),
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["names"]["zh-CN"] == "鳄梨"
    assert updated["visualKey"] == "mushrooms"
    assert updated["category"] == "produce"
    assert len(updated["shelfLife"]) == 2

    # Soft delete removes it from the user-facing library but keeps history.
    r = c.delete("/api/admin/foods/avocado")
    assert r.status_code == 200
    assert r.json()["active"] is False

    _register_user(c, "shopper")
    library = c.get("/api/library").json()
    assert all(item["foodKey"] != "avocado" for item in library)


def test_library_serves_admin_created_foods_to_regular_users():
    c = _client()
    _login_admin(c)
    c.post("/api/admin/foods", json=_food_payload())

    _register_user(c)
    library = c.get("/api/library").json()
    avocado = next(item for item in library if item["foodKey"] == "avocado")
    assert avocado["names"]["en"] == "Avocado"
    assert avocado["baseUnit"] == "piece"
    assert avocado["recommendedStorage"] == "FRIDGE"
    assert avocado["shelfLife"][0]["durationDays"] == 4
    assert avocado["packagePresets"][0]["amount"] == "1"


def test_invalid_food_payloads_are_rejected():
    c = _client()
    _login_admin(c)

    cases = [
        _food_payload(names={"zh-CN": "牛油果"}),
        _food_payload(baseUnit="clove"),
        _food_payload(recommendedStorage="CELLAR"),
        _food_payload(shelfLife=[{"storageLocation": "FRIDGE", "durationDays": -1}]),
        _food_payload(shelfLife=[{"storageLocation": "FRIDGE", "durationDays": 1}] * 2),
    ]
    for payload in cases:
        r = c.post("/api/admin/foods", json=payload)
        assert r.status_code in (409, 422), payload


def test_base_unit_change_converts_existing_lots():
    c = _client()
    _login_admin(c)
    c.post(
        "/api/admin/foods",
        json=_food_payload(foodKey="flour", baseUnit="kg", names={"en": "Flour", "zh-CN": "面粉"}),
    )

    _register_user(c, "baker")
    c.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "admin-test-checkin-1",
            "foodKey": "flour",
            "names": {"en": "Flour", "zh-CN": "面粉"},
            "quantity": "1.5",
            "unit": "kg",
            "location": "PANTRY",
            "storedOn": "2026-01-01",
            "expiresOn": None,
            "expirySource": "NONE",
        },
    )

    _login_admin(c)
    # Same-dimension change (kg -> g) converts the lot transactionally.
    r = c.patch(
        "/api/admin/foods/flour",
        json=_food_payload(foodKey="flour", baseUnit="g", names={"en": "Flour", "zh-CN": "面粉"}),
    )
    assert r.status_code == 200
    assert r.json()["baseUnit"] == "g"

    # The owning user's lot was converted in the same transaction.
    r = c.post("/api/auth/login", json={"username": "baker", "password": "password123"})
    assert r.status_code == 200
    r = c.get("/api/storage")
    assert r.status_code == 200
    flour = next(item for item in r.json()["inventory"] if item["foodKey"] == "flour")
    assert flour["unit"] == "g"
    assert flour["quantity"] == "1500"

    _login_admin(c)
    # Cross-dimension change while lots exist is rejected, not guessed.
    r = c.patch(
        "/api/admin/foods/flour",
        json=_food_payload(foodKey="flour", baseUnit="ml", names={"en": "Flour", "zh-CN": "面粉"}),
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_UNIT_CHANGE_CONFLICT"


def test_settings_update_controls_use_soon_window():
    from datetime import date, timedelta

    c = _client()
    _login_admin(c)

    r = c.get("/api/admin/settings")
    assert r.status_code == 200
    assert r.json()["useSoonWindowDays"] == 5

    today = date.today()
    _register_user(c, "scheduler")
    c.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "admin-test-checkin-2",
            "foodKey": "milk",
            "names": {"en": "Milk", "zh-CN": "牛奶"},
            "quantity": "1",
            "unit": "l",
            "location": "FRIDGE",
            "storedOn": today.isoformat(),
            "expiresOn": (today + timedelta(days=4)).isoformat(),
            "expirySource": "USER_OVERRIDE",
        },
    )

    # The default 5-day window keeps a 4-day lot in Use Soon.
    r = c.get("/api/storage")
    assert r.status_code == 200
    body = r.json()
    assert any(item["foodKey"] == "milk" for item in body["useSoon"])

    # Shrinking the window to 2 days removes it from Use Soon but not Storage.
    _login_admin(c)
    r = c.put("/api/admin/settings", json={"useSoonWindowDays": 2})
    assert r.status_code == 200
    assert r.json()["useSoonWindowDays"] == 2

    r = c.post("/api/auth/login", json={"username": "scheduler", "password": "password123"})
    assert r.status_code == 200
    body = c.get("/api/storage").json()
    assert all(item["foodKey"] != "milk" for item in body["useSoon"])
    assert any(item["foodKey"] == "milk" for item in body["inventory"])

    # Out-of-range values are rejected (pydantic 422 for < 1, service 409 for > 30).
    _login_admin(c)
    assert c.put("/api/admin/settings", json={"useSoonWindowDays": 0}).status_code == 422
    assert c.put("/api/admin/settings", json={"useSoonWindowDays": 31}).status_code == 409


def _upload_icon(c: TestClient, food_id: str, content: bytes, filename: str, content_type: str):
    return c.post(
        f"/api/admin/foods/{food_id}/icon",
        files={"file": (filename, content, content_type)},
    )


def test_icon_upload_stores_sanitized_svg_and_serves_it_via_library():
    c = _client()
    _login_admin(c)
    c.post("/api/admin/foods", json=_food_payload())

    # A malicious SVG (script, event handler, external reference, foreign
    # object) must be stripped down to safe drawing content.
    evil = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
        b"<script>alert(1)</script>"
        b'<rect width="48" height="48" fill="#285f43" onclick="alert(2)"/>'
        b'<path d="M5 30 L24 8 L43 30 Z" fill="url(https://evil.example/x.png)"/>'
        b"<foreignObject><div>text</div></foreignObject>"
        b'<circle cx="24" cy="24" r="10" fill="none" stroke="#fff" stroke-width="3"/>'
        b"</svg>"
    )
    r = _upload_icon(c, "avocado", evil, "avocado.svg", "image/svg+xml")
    assert r.status_code == 201
    body = r.json()
    assert body["customIcon"].startswith("data:image/svg+xml;base64,")

    import base64 as _b64

    stored = _b64.b64decode(body["customIcon"].split(",", 1)[1]).decode("utf-8")
    assert "<script" not in stored and "foreignObject" not in stored
    assert "onclick" not in stored and "evil.example" not in stored
    assert "<rect" in stored and "<circle" in stored and "<path" in stored

    # The icon is served to regular users through the library endpoint.
    _register_user(c, "shopper")
    library = c.get("/api/library").json()
    avocado = next(item for item in library if item["foodKey"] == "avocado")
    assert avocado["customIcon"] == body["customIcon"]

    # Removing the icon restores the fallback.
    _login_admin(c)
    r = c.delete("/api/admin/foods/avocado/icon")
    assert r.status_code == 200
    assert r.json()["customIcon"] is None


def test_icon_upload_accepts_png_and_rejects_invalid_files():
    c = _client()
    _login_admin(c)
    c.post("/api/admin/foods", json=_food_payload())

    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    r = _upload_icon(c, "avocado", png, "icon.png", "image/png")
    assert r.status_code == 201
    assert r.json()["customIcon"].startswith("data:image/png;base64,")

    # Fake PNG magic is rejected.
    r = _upload_icon(c, "avocado", b"not a png at all", "icon.png", "image/png")
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_ICON_INVALID"

    # Unsupported format is rejected.
    r = _upload_icon(c, "avocado", b"GIF89a\x00\x00", "icon.gif", "image/gif")
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_ICON_INVALID"

    # Malformed SVG is rejected.
    r = _upload_icon(c, "avocado", b"<svg><path", "icon.svg", "image/svg+xml")
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_ICON_INVALID"


def test_icon_upload_rejects_oversized_files():
    c = _client()
    _login_admin(c)
    c.post("/api/admin/foods", json=_food_payload())

    big = b"<svg></svg>" + b"x" * (100 * 1024)
    r = _upload_icon(c, "avocado", big, "icon.svg", "image/svg+xml")
    assert r.status_code == 409
    assert r.json()["detail"] == "ADMIN_ICON_TOO_LARGE"


def test_icon_upload_requires_admin_and_existing_food():
    c = _client()
    _register_user(c)
    r = _upload_icon(c, "avocado", b"<svg></svg>", "icon.svg", "image/svg+xml")
    assert r.status_code == 403
    assert r.json()["detail"] == "ADMIN_REQUIRED"

    _login_admin(c)
    r = _upload_icon(c, "missing-food", b"<svg></svg>", "icon.svg", "image/svg+xml")
    assert r.status_code == 404
    assert r.json()["detail"] == "ADMIN_FOOD_NOT_FOUND"


def test_admin_cannot_list_or_mutate_a_personal_food_definition():
    c = _client()
    _register_user(c, "personal-owner")
    created = c.post(
        "/api/inventory/check-in",
        json={
            "idempotencyKey": "personal-admin-isolation",
            "foodKey": "custom:personal-admin-food",
            "names": {"en": "Personal Admin Food", "zh-CN": "个人管理食材"},
            "quantity": "1",
            "unit": "piece",
            "location": "FRIDGE",
            "storedOn": "2026-08-07",
            "expirySource": "NONE",
        },
    )
    assert created.status_code == 201
    personal_food_key = next(
        item["foodKey"]
        for item in c.get("/api/storage").json()["inventory"]
        if item["names"]["en"] == "Personal Admin Food"
    )

    _login_admin(c)
    foods = c.get("/api/admin/foods").json()
    assert all(
        food["foodKey"] != personal_food_key and food["names"]["en"] != "Personal Admin Food"
        for food in foods
    )

    update = c.patch(f"/api/admin/foods/{personal_food_key}", json=_food_payload())
    delete = c.delete(f"/api/admin/foods/{personal_food_key}")
    upload = _upload_icon(c, personal_food_key, b"<svg></svg>", "icon.svg", "image/svg+xml")
    remove = c.delete(f"/api/admin/foods/{personal_food_key}/icon")
    for response in (update, delete, upload, remove):
        assert response.status_code == 404
        assert response.json()["detail"] == "ADMIN_FOOD_NOT_FOUND"
