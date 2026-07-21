"""Deterministic fixture adapters for tests and offline demo (contract 12).

Same input always yields the same output: a normalized recipe generated from
the selected ingredients. No network, no credentials.
"""

from app.domain.recipe import PROVENANCE_AI_INFERENCE
from app.domain.types import IngredientAmountKind, RecipeAnalysisStatus
from app.infrastructure.recipe.schemas import (
    RECIPE_SCHEMA_VERSION,
    NormalizedIngredient,
    NormalizedRecipe,
    StructuringRequest,
)


class FixtureStructuringAdapter:
    """Deterministic structuring fixture."""

    def structure(self, request: StructuringRequest) -> NormalizedRecipe:
        first_name = request.ingredients[0].name
        cuisine_suffix = f" ({request.cuisine} style)" if request.cuisine else ""

        ingredients = [
            NormalizedIngredient(
                original_text=ing.name,
                amount_kind=IngredientAmountKind.NUMERIC,
                amount=ing.quantity,
                unit=ing.unit,
                mapping_suggestion=ing.food_definition_id,
                provenance=PROVENANCE_AI_INFERENCE,
            )
            for ing in request.ingredients
        ]
        return NormalizedRecipe(
            schema_version=RECIPE_SCHEMA_VERSION,
            title=f"Creative {first_name} skillet{cuisine_suffix}",
            description=(
                f"An original recipe built around {first_name}"
                " and your selected ingredients."
            ),
            base_yield=request.servings,
            ingredients=ingredients,
            steps=[
                f"Prep the {first_name}: wash, trim, and cut into bite-sized pieces.",
                (
                    f"Heat oil in a pan over medium-high heat."
                    f" Cook the {first_name} for 3-4 minutes until lightly browned."
                ),
                (
                    "Add remaining ingredients and stir-fry for another"
                    " 2-3 minutes until tender but not overcooked."
                ),
                (
                    "Season with salt, pepper, and any preferred herbs."
                    " Serve immediately while hot."
                ),
            ],
            source_urls=[],
            analysis_status=RecipeAnalysisStatus.READY,
            warnings=[],
        )
