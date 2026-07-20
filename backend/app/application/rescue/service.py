from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.orm import Session

from app.infrastructure.db.models import RescueSessionRow
from app.infrastructure.recipe.errors import RecipeAdapterError
from app.infrastructure.recipe.factory import RecipeAdapters
from app.infrastructure.recipe.schemas import (
    RetrievalIngredientInput,
    RetrievalRequest,
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


@dataclass(frozen=True)
class SearchResult:
    session_id: str
    sources: list[dict[str, object]]
    ai_plan: dict[str, object] | None
    ai_plan_error: str | None


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

    retrieval_request = RetrievalRequest(
        ingredients=ingredient_inputs,
        servings=command.servings,
        locale=command.locale,
    )

    response = adapters.retrieval.retrieve(retrieval_request)

    sources: list[dict[str, object]] = []
    for i, src in enumerate(response.sources):
        sources.append(
            {
                "id": f"source-{i}",
                "url": src.url,
                "title": src.title,
                "publisher": src.publisher,
                "domain": urlparse(src.url).netloc,
                "retrievedAt": src.retrieved_at.isoformat(),
                "baseYield": src.base_yield,
                "usedFoodKeys": src.used_food_ids,
            }
        )

    ai_plan: dict[str, object] | None = None
    ai_plan_error: str | None = None

    try:
        structuring_request = StructuringRequest(
            sources=response.sources,
            ingredients=ingredient_inputs,
            servings=command.servings,
            locale=command.locale,
        )
        recipe = adapters.structuring.structure(structuring_request)

        ai_plan = {
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
    except RecipeAdapterError as error:
        ai_plan = None
        ai_plan_error = str(error.code.value)
    except Exception:
        ai_plan = None
        ai_plan_error = "ERR-02"

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
        source_results=sources,
        ai_plan=ai_plan,
        ai_plan_error=ai_plan_error,
        searched_at=datetime.now(UTC),
    )
    session.add(row)
    session.commit()

    return SearchResult(
        session_id=row.id,
        sources=sources,
        ai_plan=ai_plan,
        ai_plan_error=ai_plan_error,
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
        "sources": row.source_results,
        "aiPlan": row.ai_plan,
        "aiPlanError": row.ai_plan_error,
        "createdAt": row.created_at.isoformat(),
        "searchedAt": row.searched_at.isoformat() if row.searched_at else None,
    }
