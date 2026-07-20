from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.rescue.service import (
    SearchCommand,
    SelectedFoodSnapshot,
    get_rescue_session,
    search_recipe_sources,
)
from app.infrastructure.recipe.errors import RecipeAdapterError
from app.infrastructure.recipe.factory import RecipeAdapters


class SelectedFoodInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    food_key: str = Field(alias="foodKey", min_length=1, max_length=100)
    names: dict[str, str]
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    location: str
    urgency: str


class SearchRecipeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selected_foods: list[SelectedFoodInput] = Field(
        alias="selectedFoods", min_length=1, max_length=7
    )
    servings: int = Field(default=2, ge=1, le=20)
    locale: str = Field(default="en")


def build_rescue_router(session_provider, adapters: RecipeAdapters) -> APIRouter:
    api = APIRouter()

    @api.post("/rescue/search")
    def search(
        payload: SearchRecipeRequest,
        session: Annotated[Session, Depends(session_provider)],
    ) -> dict[str, object]:
        try:
            result = search_recipe_sources(
                session,
                SearchCommand(
                    selected_foods=[
                        SelectedFoodSnapshot(
                            food_key=food.food_key,
                            names=food.names,
                            quantity=food.quantity,
                            unit=food.unit,
                            location=food.location,
                            urgency=food.urgency,
                        )
                        for food in payload.selected_foods
                    ],
                    servings=payload.servings,
                    locale=payload.locale,
                ),
                adapters,
            )
        except RecipeAdapterError as error:
            session.rollback()
            mapping = {
                "ERR-01": status.HTTP_504_GATEWAY_TIMEOUT,
                "ERR-03": status.HTTP_404_NOT_FOUND,
                "ERR-04": status.HTTP_503_SERVICE_UNAVAILABLE,
            }
            raise HTTPException(
                status_code=mapping.get(str(error.code.value), status.HTTP_503_SERVICE_UNAVAILABLE),
                detail=str(error),
            ) from error

        return {
            "sessionId": result.session_id,
            "sources": result.sources,
            "aiPlan": result.ai_plan,
            "aiPlanError": result.ai_plan_error,
        }

    @api.get("/rescue/{session_id}")
    def get_session(
        session_id: str,
        session: Annotated[Session, Depends(session_provider)],
    ) -> dict[str, object]:
        result = get_rescue_session(session, session_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
        return result

    return api
