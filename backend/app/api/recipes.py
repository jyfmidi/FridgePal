from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.recipes.service import (
    SaveRecipeCommand,
    get_recipe,
    list_recipes,
    save_recipe,
)
from app.auth.service import UserContext


class RecipeIngredientInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1, max_length=100)
    name_key: str = Field(alias="nameKey", min_length=1, max_length=100)
    food_key: str | None = Field(default=None, alias="foodKey")
    base_amount: str = Field(alias="baseAmount", min_length=1, max_length=50)


class SaveRecipeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    base_yield: int = Field(alias="baseYield", ge=1, le=100)
    multiplier: float = Field(default=1.0, gt=0, le=10)
    ingredients: list[RecipeIngredientInput] = Field(min_length=1)
    instructions: list[str] = Field(min_length=1)
    origin_type: str = Field(alias="originType", default="personal")
    origin_id: str | None = Field(default=None, alias="originId")
    source_url: str | None = Field(default=None, alias="sourceUrl", max_length=500)
    source_publisher: str | None = Field(default=None, alias="sourcePublisher", max_length=200)


def build_recipe_router(session_provider, current_user) -> APIRouter:
    api = APIRouter()

    @api.get("/recipes")
    def list_all(
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, list[dict[str, object]]]:
        return {"recipes": list_recipes(session, user.user_id)}

    @api.get("/recipes/{recipe_id}")
    def get_one(
        recipe_id: str,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        result = get_recipe(session, user.user_id, recipe_id)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="recipe not found")
        return result

    @api.post("/recipes")
    def create(
        payload: SaveRecipeRequest,
        response: Response,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        result = save_recipe(
            session,
            user.user_id,
            SaveRecipeCommand(
                id=payload.id,
                name=payload.name,
                description=payload.description,
                base_yield=payload.base_yield,
                multiplier=payload.multiplier,
                ingredients=[
                    {
                        "id": ing.id,
                        "nameKey": ing.name_key,
                        "foodKey": ing.food_key,
                        "baseAmount": ing.base_amount,
                    }
                    for ing in payload.ingredients
                ],
                instructions=payload.instructions,
                origin_type=payload.origin_type,
                origin_id=payload.origin_id,
                source_url=payload.source_url,
                source_publisher=payload.source_publisher,
            ),
        )
        if result.created:
            response.status_code = status.HTTP_201_CREATED
        return {"id": result.id, "created": result.created}

    @api.patch("/recipes/{recipe_id}", status_code=status.HTTP_200_OK)
    def update(
        recipe_id: str,
        payload: SaveRecipeRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        result = save_recipe(
            session,
            user.user_id,
            SaveRecipeCommand(
                id=recipe_id,
                name=payload.name,
                description=payload.description,
                base_yield=payload.base_yield,
                multiplier=payload.multiplier,
                ingredients=[
                    {
                        "id": ing.id,
                        "nameKey": ing.name_key,
                        "foodKey": ing.food_key,
                        "baseAmount": ing.base_amount,
                    }
                    for ing in payload.ingredients
                ],
                instructions=payload.instructions,
                origin_type=payload.origin_type,
                origin_id=payload.origin_id,
                source_url=payload.source_url,
                source_publisher=payload.source_publisher,
            ),
        )
        return {"id": result.id, "created": result.created}

    return api
