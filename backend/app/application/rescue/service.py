from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import RescueSessionRow
from app.infrastructure.recipe.errors import RecipeAdapterError
from app.infrastructure.recipe.factory import RecipeAdapters
from app.infrastructure.recipe.schemas import (
    RetrievalIngredientInput,
    StructuringRequest,
    format_quantity,
)


@dataclass(frozen=True)
class SelectedFoodSnapshot:
    food_key: str
    names: dict[str, str]
    quantity: Decimal
    unit: str
    location: str
    urgency: str


@dataclass(frozen=True)
class SearchCommand:
    selected_foods: list[SelectedFoodSnapshot]
    servings: int
    locale: str
    cuisine: str


@dataclass(frozen=True)
class SearchResult:
    session_id: str
    recipes: list[dict[str, object]]
    recipe_errors: list[str]


def _serialize_recipe(recipe: Any) -> dict[str, object]:
    return {
        "title": recipe.title,
        "description": recipe.description,
        "baseYield": recipe.base_yield,
        "ingredients": [
            {
                "originalText": ing.original_text,
                "amountKind": ing.amount_kind.value,
                "amount": format_quantity(ing.amount) if ing.amount is not None else None,
                "unit": ing.unit,
                "mappingSuggestion": ing.mapping_suggestion,
                "provenance": ing.provenance,
                "needsReview": ing.needs_review,
            }
            for ing in recipe.ingredients
        ],
        "steps": recipe.steps,
        "sourceUrls": recipe.source_urls,
        "analysisStatus": recipe.analysis_status.value,
        "warnings": recipe.warnings,
    }


def _normalize_food_key(key: str) -> str:
    return key.lower().replace("-", " ").replace("_", " ").strip()


def _build_name_index(ingredient_inputs: list[RetrievalIngredientInput]) -> dict[str, str]:
    index: dict[str, str] = {}
    for ing in ingredient_inputs:
        normalized = _normalize_food_key(ing.food_definition_id)
        index[normalized] = ing.food_definition_id
        index[_normalize_food_key(ing.name)] = ing.food_definition_id
        for word in normalized.split():
            if len(word) > 2:
                index[word] = ing.food_definition_id
        if normalized.endswith("s"):
            index[normalized[:-1]] = ing.food_definition_id
        else:
            index[normalized + "s"] = ing.food_definition_id
    return index


def _map_ingredient_food_keys(
    recipe: Any, name_index: dict[str, str]
) -> None:
    """Set mapping_suggestion to the matched food_definition_id for each ingredient."""
    valid_ids = set(name_index.values())
    for recipe_ing in recipe.ingredients:
        if recipe_ing.mapping_suggestion and recipe_ing.mapping_suggestion in valid_ids:
            continue
        text = _normalize_food_key(recipe_ing.original_text)
        suggestion = _normalize_food_key(recipe_ing.mapping_suggestion or "")
        for name, food_id in name_index.items():
            if name in text or name in suggestion or text in name:
                recipe_ing.mapping_suggestion = food_id
                break


def search_recipe_sources(
    session: Session,
    command: SearchCommand,
    adapters: RecipeAdapters,
) -> SearchResult:
    ingredient_inputs: list[RetrievalIngredientInput] = []
    for food in command.selected_foods:
        name = food.names.get(command.locale) or food.names.get("en") or food.food_key
        ingredient_inputs.append(
            RetrievalIngredientInput(
                food_definition_id=food.food_key,
                name=name,
                quantity=food.quantity,
                unit=food.unit,
            )
        )

    name_index = _build_name_index(ingredient_inputs)

    recipes: list[dict[str, object]] = []
    recipe_errors: list[str] = []

    for _i in range(2):
        try:
            structuring_request = StructuringRequest(
                ingredients=ingredient_inputs,
                servings=command.servings,
                locale=command.locale,
                cuisine=command.cuisine,
            )
            recipe = adapters.structuring.structure(structuring_request)
            _map_ingredient_food_keys(recipe, name_index)
            recipes.append(_serialize_recipe(recipe))
        except RecipeAdapterError as error:
            recipe_errors.append(str(error.code.value))
        except Exception:
            recipe_errors.append("ERR-02")

    selected_foods_json: list[dict[str, Any]] = [
        {
            "foodKey": f.food_key,
            "names": f.names,
            "quantity": str(f.quantity),
            "unit": f.unit,
            "location": f.location,
            "urgency": f.urgency,
        }
        for f in command.selected_foods
    ]

    row = RescueSessionRow(
        id=str(uuid4()),
        status="SEARCHED",
        selected_foods=selected_foods_json,
        servings=command.servings,
        locale=command.locale,
        cuisine=command.cuisine,
        source_results=recipes,
        ai_plan=recipes[0] if recipes else None,
        ai_plan_error=recipe_errors[0] if recipe_errors and not recipes else None,
        source_analyses=None,
        searched_at=datetime.now(UTC),
    )
    session.add(row)
    session.commit()

    return SearchResult(
        session_id=row.id,
        recipes=recipes,
        recipe_errors=recipe_errors,
    )


def get_rescue_session(session: Session, session_id: str) -> dict[str, object] | None:
    row = session.get(RescueSessionRow, session_id)
    if row is None:
        return None

    return {
        "sessionId": row.id,
        "status": row.status,
        "selectedFoods": row.selected_foods,
        "servings": row.servings,
        "locale": row.locale,
        "cuisine": row.cuisine,
        "recipes": row.source_results,
        "aiPlan": row.ai_plan,
        "aiPlanError": row.ai_plan_error,
        "sourceAnalyses": row.source_analyses,
        "createdAt": row.created_at.isoformat(),
        "searchedAt": row.searched_at.isoformat() if row.searched_at else None,
    }


def list_rescue_sessions(session: Session, limit: int = 3) -> list[dict[str, object]]:
    rows = session.execute(
        select(RescueSessionRow)
        .where(RescueSessionRow.source_results.isnot(None))
        .order_by(RescueSessionRow.created_at.desc())
        .limit(limit)
    ).scalars().all()

    return [
        {
            "sessionId": row.id,
            "selectedFoods": row.selected_foods,
            "servings": row.servings,
            "locale": row.locale,
            "cuisine": row.cuisine,
            "recipes": row.source_results,
            "aiPlan": row.ai_plan,
            "aiPlanError": row.ai_plan_error,
            "sourceAnalyses": row.source_analyses,
            "createdAt": row.created_at.isoformat(),
            "searchedAt": row.searched_at.isoformat() if row.searched_at else None,
        }
        for row in rows
    ]
