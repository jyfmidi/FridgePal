"""Contract tests for the rescue search API pipeline."""

from pathlib import Path

from app.config import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


def _search_payload() -> dict:
    return {
        "selectedFoods": [
            {
                "foodKey": "spinach",
                "names": {"en": "Spinach"},
                "quantity": "200",
                "unit": "g",
                "location": "FRIDGE",
                "urgency": "LATER",
            },
            {
                "foodKey": "tofu",
                "names": {"en": "Tofu"},
                "quantity": "150",
                "unit": "g",
                "location": "FRIDGE",
                "urgency": "LATER",
            },
        ],
        "servings": 2,
        "locale": "en",
    }


def test_search_returns_recipes_in_fixture_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/api/rescue/search", json=_search_payload())

    assert response.status_code == 200
    data = response.json()

    assert "sessionId" in data
    assert isinstance(data["sessionId"], str)
    assert len(data["sessionId"]) > 0

    assert "recipes" in data
    assert isinstance(data["recipes"], list)
    assert len(data["recipes"]) == 2

    for recipe in data["recipes"]:
        assert "title" in recipe
        assert "description" in recipe
        assert "baseYield" in recipe
        assert "ingredients" in recipe
        assert "steps" in recipe
        assert "sourceUrls" in recipe
        assert "analysisStatus" in recipe
        assert "warnings" in recipe
        assert len(recipe["steps"]) >= 3

        for ing in recipe["ingredients"]:
            assert "originalText" in ing
            assert "amountKind" in ing
            assert "amount" in ing
            assert "unit" in ing
            assert "mappingSuggestion" in ing
            assert "provenance" in ing
            assert "needsReview" in ing

    assert "recipeErrors" in data
    assert len(data["recipeErrors"]) == 0

    get_settings.cache_clear()


def test_search_with_cuisine(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = {**_search_payload(), "cuisine": "Chinese"}
    response = client.post("/api/rescue/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["recipes"]) == 2
    for recipe in data["recipes"]:
        assert "Chinese" in recipe["title"]

    get_settings.cache_clear()


def test_search_persists_session_retrievable_by_id(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    search_response = client.post("/api/rescue/search", json=_search_payload())
    assert search_response.status_code == 200
    session_id = search_response.json()["sessionId"]

    get_response = client.get(f"/api/rescue/{session_id}")
    assert get_response.status_code == 200
    data = get_response.json()

    assert data["sessionId"] == session_id
    assert data["status"] == "SEARCHED"
    assert "recipes" in data
    assert data["servings"] == 2
    assert data["locale"] == "en"

    get_settings.cache_clear()


def test_search_rejects_empty_selection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = {"selectedFoods": [], "servings": 2, "locale": "en"}
    response = client.post("/api/rescue/search", json=payload)

    assert response.status_code == 422

    get_settings.cache_clear()


def test_search_rejects_more_than_seven_foods(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = {
        "selectedFoods": [
            {
                "foodKey": f"food{i}",
                "names": {"en": f"Food {i}"},
                "quantity": "100",
                "unit": "g",
                "location": "FRIDGE",
                "urgency": "LATER",
            }
            for i in range(8)
        ],
        "servings": 2,
        "locale": "en",
    }
    response = client.post("/api/rescue/search", json=payload)

    assert response.status_code == 422

    get_settings.cache_clear()


def test_get_unknown_session_returns_404(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/rescue/nonexistent-session-id")

    assert response.status_code == 404

    get_settings.cache_clear()


def test_search_is_deterministic_in_fixture_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "rescue.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    monkeypatch.setenv("RECIPE_PROVIDER_MODE", "fixture")
    get_settings.cache_clear()
    client = TestClient(create_app())

    payload = _search_payload()

    first = client.post("/api/rescue/search", json=payload)
    assert first.status_code == 200
    first_data = first.json()

    second = client.post("/api/rescue/search", json=payload)
    assert second.status_code == 200
    second_data = second.json()

    assert first_data["sessionId"] != second_data["sessionId"]

    assert len(first_data["recipes"]) == len(second_data["recipes"])
    for r1, r2 in zip(
        first_data["recipes"], second_data["recipes"], strict=True
    ):
        assert r1["title"] == r2["title"]
        assert r1["steps"] == r2["steps"]

    get_settings.cache_clear()
