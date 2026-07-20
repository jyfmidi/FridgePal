"""Contract tests for the saved recipe API."""

from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def _recipe_payload(**overrides: object) -> dict:
    payload = {
        "name": "Test recipe",
        "description": "A test recipe",
        "baseYield": 2,
        "multiplier": 1.0,
        "ingredients": [
            {
                "id": "spinach-FRIDGE",
                "nameKey": "foods.spinach",
                "foodKey": "spinach",
                "baseAmount": "200 g",
            },
        ],
        "instructions": ["Prep ingredients.", "Cook."],
        "originType": "personal",
    }
    payload.update(overrides)
    return payload


def test_create_saved_recipe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/api/recipes", json=_recipe_payload())

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["created"] is True

    get_settings.cache_clear()


def test_get_saved_recipe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    create_response = client.post("/api/recipes", json=_recipe_payload())
    assert create_response.status_code == 201
    recipe_id = create_response.json()["id"]

    get_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    assert data["id"] == recipe_id
    assert data["name"] == "Test recipe"
    assert data["description"] == "A test recipe"
    assert data["baseYield"] == 2
    assert data["multiplier"] == 1.0
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["id"] == "spinach-FRIDGE"
    assert data["instructions"] == ["Prep ingredients.", "Cook."]
    assert data["originType"] == "personal"
    assert data["lastCookedPortion"] is None
    assert "createdAt" in data
    assert "updatedAt" in data

    get_settings.cache_clear()


def test_list_saved_recipes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    client.post("/api/recipes", json=_recipe_payload(name="Recipe One"))
    client.post("/api/recipes", json=_recipe_payload(name="Recipe Two"))

    list_response = client.get("/api/recipes")
    assert list_response.status_code == 200
    data = list_response.json()

    assert "recipes" in data
    assert isinstance(data["recipes"], list)
    assert len(data["recipes"]) == 2

    get_settings.cache_clear()


def test_update_saved_recipe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    create_response = client.post("/api/recipes", json=_recipe_payload())
    assert create_response.status_code == 201
    recipe_id = create_response.json()["id"]

    update_response = client.post(
        "/api/recipes", json=_recipe_payload(id=recipe_id, name="Updated Name")
    )
    assert update_response.status_code == 200
    assert update_response.json()["created"] is False

    get_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Updated Name"

    get_settings.cache_clear()


def test_get_unknown_recipe_returns_404(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/recipes/nonexistent")

    assert response.status_code == 404

    get_settings.cache_clear()


def test_create_rejects_empty_name(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/api/recipes", json=_recipe_payload(name=""))

    assert response.status_code == 422

    get_settings.cache_clear()


def test_create_rejects_empty_ingredients(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'recipes.db'}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/api/recipes", json=_recipe_payload(ingredients=[]))

    assert response.status_code == 422

    get_settings.cache_clear()
