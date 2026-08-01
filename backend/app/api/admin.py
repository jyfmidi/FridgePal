"""HTTP boundary for administrator-only endpoints.

Every route requires an authenticated user with ``is_admin``; the frontend
maps the stable ``ADMIN_REQUIRED`` code to localized copy.
"""

from collections.abc import Callable
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.application.admin.icons import MAX_ICON_BYTES, IconValidationError, validate_icon_upload
from app.application.admin.service import (
    AdminError,
    FoodDefinitionInput,
    PackagePresetInput,
    ShelfLifeInput,
    clear_food_icon,
    create_food_definition,
    get_app_settings,
    list_food_definitions,
    set_food_icon,
    soft_delete_food_definition,
    update_app_settings,
    update_food_definition,
)
from app.auth.service import UserContext
from app.domain.inventory_unit import canonical_inventory_unit


class ShelfLifeRuleIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    storage_location: str = Field(alias="storageLocation", min_length=1, max_length=20)
    duration_days: int = Field(alias="durationDays", ge=0, le=3650)
    source_note: str | None = Field(default=None, alias="sourceNote", max_length=200)


class PackagePresetIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: dict[str, str]
    amount: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("unit")
    @classmethod
    def unit_must_be_canonical(cls, value: str) -> str:
        return canonical_inventory_unit(value)

    @field_validator("label")
    @classmethod
    def label_must_include_english(cls, value: dict[str, str]) -> dict[str, str]:
        if not value.get("en", "").strip():
            raise ValueError("label must include an English label")
        return value


class FoodDefinitionIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    food_key: str | None = Field(default=None, alias="foodKey", min_length=1, max_length=100)
    names: dict[str, str]
    aliases: dict[str, list[str]] = Field(default_factory=dict)
    category: str = Field(default="other", max_length=50)
    # Empty means "auto": the food key is used, which renders the deterministic
    # monogram unless a curated icon happens to share the key.
    visual_key: str = Field(default="", alias="visualKey", max_length=100)
    base_unit: str = Field(alias="baseUnit", min_length=1, max_length=20)
    rounding_increment: Decimal | None = Field(default=None, alias="roundingIncrement", gt=0)
    package_presets: list[PackagePresetIn] = Field(default_factory=list, alias="packagePresets")
    recommended_storage: str = Field(alias="recommendedStorage", min_length=1, max_length=20)
    active: bool = True
    shelf_life: list[ShelfLifeRuleIn] = Field(default_factory=list, alias="shelfLife")

    @field_validator("base_unit")
    @classmethod
    def base_unit_must_be_canonical(cls, value: str) -> str:
        return canonical_inventory_unit(value)

    @field_validator("names")
    @classmethod
    def names_must_include_english(cls, value: dict[str, str]) -> dict[str, str]:
        if not value.get("en", "").strip():
            raise ValueError("names must include an English display name")
        return value


class SettingsIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    use_soon_window_days: int = Field(alias="useSoonWindowDays", ge=1)


def _to_input(payload: FoodDefinitionIn) -> FoodDefinitionInput:
    return FoodDefinitionInput(
        food_key=payload.food_key,
        names=payload.names,
        aliases=payload.aliases,
        category=payload.category,
        visual_key=payload.visual_key,
        base_unit=payload.base_unit,
        rounding_increment=payload.rounding_increment,
        package_presets=[
            PackagePresetInput(
                label=preset.label,
                amount=preset.amount,
                unit=preset.unit,
            )
            for preset in payload.package_presets
        ],
        recommended_storage=payload.recommended_storage,
        active=payload.active,
        shelf_life=[
            ShelfLifeInput(
                storage_location=rule.storage_location,
                duration_days=rule.duration_days,
                source_note=rule.source_note,
            )
            for rule in payload.shelf_life
        ],
    )


def build_admin_router(session_provider, current_user: Callable[..., UserContext]) -> APIRouter:
    api = APIRouter()

    def admin_only(user: Annotated[UserContext, Depends(current_user)]) -> UserContext:
        if not user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ADMIN_REQUIRED")
        return user

    @api.get("/admin/foods")
    def foods(
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> list[dict[str, object]]:
        return list_food_definitions(session)

    @api.post("/admin/foods", status_code=status.HTTP_201_CREATED)
    def create_food(
        payload: FoodDefinitionIn,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        try:
            return create_food_definition(session, _to_input(payload))
        except AdminError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=error.code) from error

    @api.patch("/admin/foods/{food_id}")
    def update_food(
        food_id: str,
        payload: FoodDefinitionIn,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        try:
            return update_food_definition(session, food_id, _to_input(payload))
        except AdminError as error:
            session.rollback()
            code = (
                status.HTTP_404_NOT_FOUND
                if error.code == "ADMIN_FOOD_NOT_FOUND"
                else status.HTTP_409_CONFLICT
            )
            raise HTTPException(status_code=code, detail=error.code) from error

    @api.delete("/admin/foods/{food_id}")
    def delete_food(
        food_id: str,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        try:
            soft_delete_food_definition(session, food_id)
        except AdminError as error:
            session.rollback()
            raise HTTPException(status_code=404, detail=error.code) from error
        return {"foodKey": food_id, "active": False}

    @api.post("/admin/foods/{food_id}/icon", status_code=status.HTTP_201_CREATED)
    async def upload_icon(
        food_id: str,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
        file: Annotated[UploadFile, File()],
    ) -> dict[str, object]:
        # Read at most one byte past the limit so oversized uploads are cheap to reject.
        content = await file.read(MAX_ICON_BYTES + 1)
        if len(content) > MAX_ICON_BYTES:
            session.rollback()
            raise HTTPException(status_code=409, detail="ADMIN_ICON_TOO_LARGE")
        try:
            data_uri = validate_icon_upload(file.filename or "", file.content_type or "", content)
        except IconValidationError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=error.code) from error
        try:
            return set_food_icon(session, food_id, data_uri)
        except AdminError as error:
            session.rollback()
            raise HTTPException(status_code=404, detail=error.code) from error

    @api.delete("/admin/foods/{food_id}/icon")
    def remove_icon(
        food_id: str,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        try:
            return clear_food_icon(session, food_id)
        except AdminError as error:
            session.rollback()
            raise HTTPException(status_code=404, detail=error.code) from error

    @api.get("/admin/settings")
    def settings(
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        return get_app_settings(session)

    @api.put("/admin/settings")
    def update_settings(
        payload: SettingsIn,
        session: Annotated[Session, Depends(session_provider)],
        _user: Annotated[UserContext, Depends(admin_only)],
    ) -> dict[str, object]:
        try:
            return update_app_settings(session, payload.use_soon_window_days)
        except AdminError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=error.code) from error

    return api
