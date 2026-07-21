"""Application service for saved recipe persistence."""

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.models import SavedRecipeRow


@dataclass(frozen=True)
class SaveRecipeCommand:
    id: str | None  # None for create, existing ID for update
    name: str
    description: str | None
    base_yield: int
    multiplier: float
    ingredients: list[dict[str, Any]]  # [{id, nameKey, foodKey, baseAmount}]
    instructions: list[str]
    origin_type: str  # "ai-plan" | "source" | "personal"
    origin_id: str | None
    source_url: str | None
    source_publisher: str | None


@dataclass(frozen=True)
class SaveRecipeResult:
    id: str
    created: bool  # True if new, False if updated


def _serialize_recipe(row: SavedRecipeRow) -> dict[str, object]:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "baseYield": row.base_yield,
        "multiplier": row.multiplier,
        "ingredients": row.ingredients,
        "instructions": row.instructions,
        "originType": row.origin_type,
        "originId": row.origin_id,
        "sourceUrl": row.source_url,
        "sourcePublisher": row.source_publisher,
        "lastCookedPortion": row.last_cooked_portion,
        "createdAt": row.created_at.isoformat(),
        "updatedAt": row.updated_at.isoformat(),
    }


def save_recipe(session: Session, user_id: str, command: SaveRecipeCommand) -> SaveRecipeResult:
    was_found = False

    if command.id is not None:
        existing = session.scalar(
            select(SavedRecipeRow).where(
                SavedRecipeRow.id == command.id,
                SavedRecipeRow.user_id == user_id,
            )
        )
        if existing is not None:
            was_found = True
            row = existing
        else:
            row = SavedRecipeRow(id=command.id, user_id=user_id)
    else:
        row = SavedRecipeRow(id=str(uuid4()), user_id=user_id)

    row.name = command.name
    row.description = command.description
    row.base_yield = command.base_yield
    row.multiplier = command.multiplier
    row.ingredients = command.ingredients
    row.instructions = command.instructions
    row.origin_type = command.origin_type
    row.origin_id = command.origin_id
    row.source_url = command.source_url
    row.source_publisher = command.source_publisher

    session.add(row)
    session.commit()

    return SaveRecipeResult(id=row.id, created=not was_found)


def list_recipes(session: Session, user_id: str) -> list[dict[str, object]]:
    rows = session.scalars(
        select(SavedRecipeRow)
        .where(SavedRecipeRow.user_id == user_id)
        .order_by(SavedRecipeRow.created_at.desc())
    ).all()
    return [_serialize_recipe(row) for row in rows]


def get_recipe(session: Session, user_id: str, recipe_id: str) -> dict[str, object] | None:
    row = session.scalar(
        select(SavedRecipeRow).where(
            SavedRecipeRow.id == recipe_id,
            SavedRecipeRow.user_id == user_id,
        )
    )
    if row is None:
        return None
    return _serialize_recipe(row)


def update_last_cooked(session: Session, user_id: str, recipe_id: str, portion: float) -> bool:
    row = session.scalar(
        select(SavedRecipeRow).where(
            SavedRecipeRow.id == recipe_id,
            SavedRecipeRow.user_id == user_id,
        )
    )
    if row is None:
        return False
    row.last_cooked_portion = portion
    session.commit()
    return True
