"""Enum contract tests: values must match docs/DOMAIN_AND_AI_CONTRACTS.md section 2."""

from app.domain import types


def test_storage_location_values() -> None:
    assert [m.value for m in types.StorageLocation] == ["FRIDGE", "FREEZER", "PANTRY"]


def test_inventory_lot_status_values() -> None:
    assert [m.value for m in types.InventoryLotStatus] == ["ACTIVE", "DEPLETED", "DISCARDED"]


def test_expiry_source_values() -> None:
    assert [m.value for m in types.ExpirySource] == ["LIBRARY_DEFAULT", "USER_OVERRIDE", "NONE"]


def test_food_origin_values() -> None:
    assert [m.value for m in types.FoodOrigin] == ["SEEDED", "USER_CREATED"]


def test_rescue_session_status_values() -> None:
    assert [m.value for m in types.RescueSessionStatus] == [
        "DRAFT",
        "SEARCHING",
        "SEARCHED",
        "PLAN_READY",
        "COOKED",
        "ARCHIVED",
    ]


def test_recipe_origin_type_values() -> None:
    assert [m.value for m in types.RecipeOriginType] == [
        "AI_PLAN",
        "WEB_SOURCE",
        "SAVED_RECIPE",
        "PERSONAL",
    ]


def test_recipe_analysis_status_values() -> None:
    assert [m.value for m in types.RecipeAnalysisStatus] == [
        "NOT_REQUIRED",
        "PENDING",
        "PARTIAL",
        "READY",
        "FAILED",
    ]


def test_ingredient_amount_kind_values() -> None:
    assert [m.value for m in types.IngredientAmountKind] == [
        "NUMERIC",
        "QUALITATIVE",
        "UNKNOWN",
    ]


def test_ingredient_mapping_status_values() -> None:
    assert [m.value for m in types.IngredientMappingStatus] == [
        "EXACT",
        "ALIAS",
        "SUGGESTED",
        "UNRESOLVED",
    ]


def test_cooking_session_status_values() -> None:
    assert [m.value for m in types.CookingSessionStatus] == [
        "DRAFT",
        "REVIEW",
        "COMMITTED",
        "CANCELLED",
    ]


def test_inventory_reason_values() -> None:
    assert [m.value for m in types.InventoryReason] == [
        "CHECK_IN",
        "EDIT",
        "MANUAL_CONSUMPTION",
        "COOKING",
        "DISCARD",
        "MOVE",
        "REVERSAL",
    ]


def test_enums_are_string_enums() -> None:
    # Persisted as plain strings; serialized forms must equal the canonical values.
    assert types.StorageLocation.FRIDGE == "FRIDGE"
    assert isinstance(types.InventoryReason.COOKING, str)
