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


def test_search_returns_sources_and_ai_plan_in_fixture_mode(
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

    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 1

    for source in data["sources"]:
        assert "id" in source
        assert "url" in source
        assert "title" in source
        assert "publisher" in source
        assert "domain" in source
        assert "retrievedAt" in source
        assert "baseYield" in source
        assert "usedFoodKeys" in source

    assert data["aiPlan"] is not None
    ai_plan = data["aiPlan"]
    assert "title" in ai_plan
    assert "description" in ai_plan
    assert "baseYield" in ai_plan
    assert "ingredients" in ai_plan
    assert "steps" in ai_plan
    assert "sourceUrls" in ai_plan
    assert "analysisStatus" in ai_plan
    assert "warnings" in ai_plan

    assert data["aiPlanError"] is None

    for ingredient in ai_plan["ingredients"]:
        assert "originalText" in ingredient
        assert "amountKind" in ingredient
        assert "amount" in ingredient
        assert "unit" in ingredient
        assert "mappingSuggestion" in ingredient
        assert "provenance" in ingredient
        assert "needsReview" in ingredient

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
    assert data["selectedFoods"] == _search_payload()["selectedFoods"]
    assert data["servings"] == 2
    assert data["locale"] == "en"
    assert "sources" in data
    assert "aiPlan" in data
    assert "aiPlanError" in data
    assert "createdAt" in data
    assert "searchedAt" in data

    food_keys = {f["foodKey"] for f in data["selectedFoods"]}
    assert food_keys == {"spinach", "tofu"}

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

    first_response = client.post("/api/rescue/search", json=payload)
    assert first_response.status_code == 200
    first_data = first_response.json()

    second_response = client.post("/api/rescue/search", json=payload)
    assert second_response.status_code == 200
    second_data = second_response.json()

    assert first_data["sessionId"] != second_data["sessionId"]

    assert len(first_data["sources"]) == len(second_data["sources"])
    for first_source, second_source in zip(
        first_data["sources"], second_data["sources"], strict=True
    ):
        assert first_source["url"] == second_source["url"]
        assert first_source["title"] == second_source["title"]
        assert first_source["publisher"] == second_source["publisher"]
        assert first_source["domain"] == second_source["domain"]

    assert first_data["aiPlan"] is not None
    assert second_data["aiPlan"] is not None
    assert first_data["aiPlan"]["title"] == second_data["aiPlan"]["title"]
    assert first_data["aiPlan"]["steps"] == second_data["aiPlan"]["steps"]
    assert len(first_data["aiPlan"]["ingredients"]) == len(second_data["aiPlan"]["ingredients"])

    get_settings.cache_clear()
