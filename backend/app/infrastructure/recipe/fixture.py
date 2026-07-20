"""Deterministic fixture adapters for tests and offline demo (contract 12).

Same input always yields the same output: fixed retrieval timestamp, stable
source set derived from the selected ingredients, and a normalized recipe that
cites only the provided allow-list. No network, no credentials.
"""

import re
from datetime import UTC, datetime

from app.domain.recipe import PROVENANCE_SOURCE
from app.domain.types import IngredientAmountKind, RecipeAnalysisStatus
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedIngredient,
    NormalizedRecipe,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedSource,
    StructuringRequest,
    format_quantity,
)

_FIXTURE_RETRIEVED_AT = datetime(2026, 1, 1, tzinfo=UTC)

# Three deterministic source patterns (publishers vary; content is synthetic).
_PATTERNS = (
    ("pantry-journal.example", "Everyday"),
    ("home-kitchen.example", "Simple"),
    ("weeknight-table.example", "Quick"),
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "food"


class FixtureRetrievalAdapter:
    """Deterministic retrieval fixture."""

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        slug = "-".join(_slug(ing.name) for ing in request.ingredients[:3])
        sources = [
            RetrievedSource(
                url=f"https://{publisher}/recipes/{label.lower()}-{slug}",
                title=f"{label} {request.ingredients[0].name} recipe",
                publisher=publisher,
                retrieved_at=_FIXTURE_RETRIEVED_AT,
                base_yield=4,
                used_food_ids=[ing.food_definition_id for ing in request.ingredients[:2]],
            )
            for publisher, label in _PATTERNS[: request.max_candidates]
        ]
        return RetrievalResponse(
            sources=sources,
            diagnostics={"mode": "fixture", "result_count": str(len(sources))},
        )


class FixtureStructuringAdapter:
    """Deterministic structuring fixture citing only allow-listed sources."""

    def structure(self, request: StructuringRequest) -> NormalizedRecipe:
        primary = request.sources[0]
        ingredients = [
            NormalizedIngredient(
                original_text=f"{format_quantity(ing.quantity)}{ing.unit} {ing.name}",
                amount_kind=IngredientAmountKind.NUMERIC,
                amount=ing.quantity,
                unit=ing.unit,
                mapping_suggestion=ing.food_definition_id,
                provenance=PROVENANCE_SOURCE,
            )
            for ing in request.ingredients
        ]
        return NormalizedRecipe(
            schema_version=RECIPE_SCHEMA_VERSION,
            title=f"Fixture {request.ingredients[0].name} for {request.servings}",
            description=f"Deterministic fixture recipe grounded in {primary.url}",
            base_yield=request.servings,
            ingredients=ingredients,
            steps=[
                f"Prepare the {request.ingredients[0].name}.",
                "Combine all ingredients and cook until done.",
            ],
            source_urls=[src.url for src in request.sources[:1]],
            analysis_status=RecipeAnalysisStatus.READY,
            warnings=[],
        )
