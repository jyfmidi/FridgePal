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
    """Deterministic structuring fixture.

    The same request always yields the same output. When ``previous_title`` is
    set (the service's second candidate), a different cooking-method template
    is used so fixture-mode demos also show two distinct dishes.
    """

    def structure(self, request: StructuringRequest) -> NormalizedRecipe:
        first_name = request.ingredients[0].name
        cuisine_suffix = f" ({request.cuisine} style)" if request.cuisine else ""
        second_candidate = bool(request.previous_title)

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
        if second_candidate:
            return NormalizedRecipe(
                schema_version=RECIPE_SCHEMA_VERSION,
                title=f"Oven-baked {first_name} traybake{cuisine_suffix}",
                description=(
                    f"An original oven-baked dish built around {first_name}"
                    " and your selected ingredients."
                ),
                base_yield=request.servings,
                ingredients=ingredients,
                steps=[
                    f"Prep the {first_name}: wash, trim, and cut into even pieces.",
                    (
                        f"Preheat the oven to 200°C (400°F). Toss the {first_name}"
                        " and remaining ingredients with oil, salt, and pepper on"
                        " a baking tray."
                    ),
                    (
                        "Roast for 20-25 minutes, turning once, until golden at"
                        " the edges and cooked through."
                    ),
                    ("Rest for 2 minutes, season to taste, and serve directly from the tray."),
                ],
                source_urls=[],
                analysis_status=RecipeAnalysisStatus.READY,
                warnings=[],
            )
        return NormalizedRecipe(
            schema_version=RECIPE_SCHEMA_VERSION,
            title=f"Creative {first_name} skillet{cuisine_suffix}",
            description=(
                f"An original recipe built around {first_name} and your selected ingredients."
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
                ("Season with salt, pepper, and any preferred herbs. Serve immediately while hot."),
            ],
            source_urls=[],
            analysis_status=RecipeAnalysisStatus.READY,
            warnings=[],
        )
