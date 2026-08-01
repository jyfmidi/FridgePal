"""Similarity guard for the two generated recipe candidates per rescue search."""

from decimal import Decimal

from app.application.rescue.service import _recipes_too_similar, _title_similarity
from app.domain.recipe import PROVENANCE_AI_INFERENCE
from app.domain.types import IngredientAmountKind, RecipeAnalysisStatus
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedIngredient,
    NormalizedRecipe,
)


def _recipe(title: str, mapped_ids: list[str] | None = None) -> NormalizedRecipe:
    ingredients = []
    for food_id in mapped_ids or []:
        ingredients.append(
            NormalizedIngredient(
                original_text=food_id,
                amount_kind=IngredientAmountKind.NUMERIC,
                amount=Decimal("100"),
                unit="g",
                mapping_suggestion=food_id,
                provenance=PROVENANCE_AI_INFERENCE,
            )
        )
    return NormalizedRecipe(
        schema_version=RECIPE_SCHEMA_VERSION,
        title=title,
        description=None,
        base_yield=2,
        ingredients=ingredients
        or [
            NormalizedIngredient(
                original_text="Kale",
                amount_kind=IngredientAmountKind.QUALITATIVE,
                provenance=PROVENANCE_AI_INFERENCE,
            )
        ],
        steps=["Step one", "Step two", "Step three"],
        source_urls=[],
        analysis_status=RecipeAnalysisStatus.READY,
        warnings=[],
    )


def test_identical_normalized_titles_are_similar() -> None:
    assert _recipes_too_similar(_recipe("Kale stir fry"), _recipe("Kale Stir-Fry!"))


def test_same_ingredients_with_near_identical_title_are_similar() -> None:
    ids = ["food-kale", "food-tofu"]
    assert _recipes_too_similar(
        _recipe("Kale and tofu skillet", ids),
        _recipe("Tofu kale skillet dinner", ids),
    )


def test_same_ingredients_with_distinct_title_are_not_similar() -> None:
    ids = ["food-kale", "food-tofu"]
    assert not _recipes_too_similar(
        _recipe("Kale and tofu skillet", ids),
        _recipe("Creamy tofu bake", ids),
    )


def test_distinct_ingredients_are_not_similar_even_with_close_titles() -> None:
    assert not _recipes_too_similar(
        _recipe("Chicken and rice soup", ["food-chicken"]),
        _recipe("Chicken soup", ["food-chicken", "food-carrot"]),
    )


def test_title_similarity_handles_chinese() -> None:
    assert _title_similarity("鸡胸肉炒菠菜", "鸡胸肉炒菠菜") == 1.0
    assert _title_similarity("鸡胸肉炒菠菜", "烤鸡胸肉配菠菜") < 0.6
    assert _recipes_too_similar(_recipe("鸡胸肉炒菠菜"), _recipe("鸡胸肉炒菠菜"))
    assert not _recipes_too_similar(_recipe("鸡胸肉炒菠菜"), _recipe("烤鸡胸肉配菠菜"))


def test_empty_mappings_fall_back_to_title_only() -> None:
    assert _recipes_too_similar(_recipe("Mushroom soup"), _recipe("Mushroom Soup"))
    assert not _recipes_too_similar(_recipe("Mushroom soup"), _recipe("Lemon cake"))
