"""HTTP boundary for the minimal Storage vertical slice."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.application.inventory.service import (
    CheckInCommand,
    CommitAllocation,
    CommitLine,
    CookingCommitCommand,
    EditLotCommand,
    LotNotFoundError,
    PreviewItem,
    ReduceCommand,
    check_in_food,
    cooking_commit,
    cooking_preview,
    decimal_string,
    discard_lot,
    edit_lot,
    get_storage_overview,
    list_lots,
    reduce_inventory,
)
from app.auth.service import UserContext
from app.domain.errors import DomainError
from app.domain.inventory_unit import canonical_inventory_unit
from app.domain.types import ExpirySource, StorageLocation

router = APIRouter()


class CheckInRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)
    food_key: str = Field(alias="foodKey", min_length=1, max_length=100)
    names: dict[str, str]
    quantity: Decimal
    unit: str = Field(min_length=1, max_length=20)
    location: StorageLocation
    stored_on: date = Field(alias="storedOn")
    expires_on: date | None = Field(default=None, alias="expiresOn")
    expiry_source: ExpirySource = Field(alias="expirySource")

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("quantity must be positive")
        return value

    @field_validator("unit")
    @classmethod
    def unit_must_be_canonical(cls, value: str) -> str:
        return canonical_inventory_unit(value)

    @field_validator("names")
    @classmethod
    def names_must_include_english(cls, value: dict[str, str]) -> dict[str, str]:
        if not value.get("en", "").strip():
            raise ValueError("names must include an English display name")
        return value


class EditLotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    location: StorageLocation | None = None
    stored_on: date | None = Field(default=None, alias="storedOn")
    expires_on: date | None = Field(default=None, alias="expiresOn")

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return canonical_inventory_unit(value)

    @field_validator("stored_on")
    @classmethod
    def stored_on_cannot_be_cleared(cls, value: date | None) -> date | None:
        if value is None:
            raise ValueError("storedOn cannot be empty")
        return value

    @model_validator(mode="after")
    def at_least_one_editable_field(self) -> "EditLotRequest":
        if (
            self.quantity is None
            and self.unit is None
            and self.location is None
            and "stored_on" not in self.model_fields_set
            and "expires_on" not in self.model_fields_set
        ):
            raise ValueError("at least one editable field is required")
        return self


class ReduceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)
    food_key: str = Field(alias="foodKey", min_length=1, max_length=100)
    location: StorageLocation
    amount: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("unit")
    @classmethod
    def unit_must_be_canonical(cls, value: str) -> str:
        return canonical_inventory_unit(value)


class DiscardRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)


class CookingPreviewItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    food_key: str = Field(alias="foodKey", min_length=1, max_length=100)
    amount: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)

    @field_validator("unit")
    @classmethod
    def unit_must_be_canonical(cls, value: str) -> str:
        return canonical_inventory_unit(value)


class CookingPreviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: list[CookingPreviewItem] = Field(min_length=1)
    location: StorageLocation | None = None


class CookingCommitAllocation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lot_id: str = Field(alias="lotId", min_length=1, max_length=36)
    quantity: Decimal = Field(gt=0)
    lot_quantity: Decimal = Field(alias="lotQuantity", ge=0)


class CookingCommitLine(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    food_key: str = Field(alias="foodKey", min_length=1, max_length=100)
    allocations: list[CookingCommitAllocation] = Field(min_length=1)


class CookingCommitRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    idempotency_key: str = Field(alias="idempotencyKey", min_length=1, max_length=120)
    session_name: str | None = Field(default=None, alias="sessionName", max_length=200)
    lines: list[CookingCommitLine] = Field(min_length=1)


def build_inventory_router(session_provider, current_user) -> APIRouter:
    api = APIRouter()

    @api.post("/inventory/check-in", status_code=status.HTTP_201_CREATED)
    def check_in(
        payload: CheckInRequest,
        response: Response,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            result = check_in_food(
                session,
                user.user_id,
                CheckInCommand(
                    idempotency_key=payload.idempotency_key,
                    food_key=payload.food_key,
                    names=payload.names,
                    quantity=payload.quantity,
                    unit=payload.unit,
                    location=payload.location.value,
                    stored_on=payload.stored_on,
                    expires_on=payload.expires_on,
                    expiry_source=payload.expiry_source.value,
                ),
            )
        except (ValueError, DomainError) as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error
        if result.replayed:
            response.status_code = status.HTTP_200_OK
        return {
            "lotId": result.lot_id,
            "activityEventId": result.activity_event_id,
            "replayed": result.replayed,
        }

    @api.get("/storage")
    def storage_overview(
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
        today: Annotated[date | None, Query()] = None,
    ) -> dict[str, list[dict[str, object]]]:
        return get_storage_overview(session, user.user_id, today or date.today())

    @api.get("/inventory/lots")
    def lots(
        session: Annotated[Session, Depends(session_provider)],
        food_key: Annotated[str, Query(alias="foodKey", min_length=1, max_length=100)],
        location: Annotated[StorageLocation, Query()],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, list[dict[str, object]]]:
        return list_lots(session, user.user_id, food_key, location.value)

    @api.patch("/lots/{lot_id}")
    def patch_lot(
        lot_id: str,
        payload: EditLotRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            result = edit_lot(
                session,
                user.user_id,
                EditLotCommand(
                    idempotency_key=payload.idempotency_key,
                    lot_id=lot_id,
                    quantity=payload.quantity,
                    unit=payload.unit,
                    location=payload.location.value if payload.location else None,
                    stored_on=payload.stored_on,
                    stored_on_provided="stored_on" in payload.model_fields_set,
                    expires_on=payload.expires_on,
                    expires_on_provided="expires_on" in payload.model_fields_set,
                ),
            )
        except LotNotFoundError as error:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(error)) from error
        except (ValueError, DomainError) as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"lotId": result.lot_id, "replayed": result.replayed}

    @api.post("/inventory/reduce")
    def reduce(
        payload: ReduceRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            result = reduce_inventory(
                session,
                user.user_id,
                ReduceCommand(
                    idempotency_key=payload.idempotency_key,
                    food_key=payload.food_key,
                    location=payload.location.value,
                    amount=payload.amount,
                    unit=payload.unit,
                ),
            )
        except (ValueError, DomainError) as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error
        body: dict[str, object] = {
            "newQuantity": decimal_string(result.new_quantity),
            "replayed": result.replayed,
        }
        if not result.replayed:
            body["allocations"] = [
                {"lotId": allocation.lot_id, "deducted": decimal_string(allocation.deducted)}
                for allocation in result.allocations
            ]
        return body

    @api.post("/lots/{lot_id}/discard")
    def discard(
        lot_id: str,
        payload: DiscardRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            result = discard_lot(session, user.user_id, lot_id, payload.idempotency_key)
        except LotNotFoundError as error:
            session.rollback()
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"lotId": result.lot_id, "replayed": result.replayed}

    @api.post("/cooking/preview")
    def preview(
        payload: CookingPreviewRequest,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            return cooking_preview(
                session,
                user.user_id,
                [
                    PreviewItem(food_key=item.food_key, amount=item.amount, unit=item.unit)
                    for item in payload.items
                ],
                payload.location.value if payload.location else None,
            )
        except (ValueError, DomainError) as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error

    @api.post("/cooking/commit", status_code=status.HTTP_201_CREATED)
    def commit(
        payload: CookingCommitRequest,
        response: Response,
        session: Annotated[Session, Depends(session_provider)],
        user: Annotated[UserContext, Depends(current_user)],
    ) -> dict[str, object]:
        try:
            result = cooking_commit(
                session,
                user.user_id,
                CookingCommitCommand(
                    idempotency_key=payload.idempotency_key,
                    session_name=payload.session_name,
                    lines=tuple(
                        CommitLine(
                            food_key=line.food_key,
                            allocations=tuple(
                                CommitAllocation(
                                    lot_id=allocation.lot_id,
                                    quantity=allocation.quantity,
                                    lot_quantity=allocation.lot_quantity,
                                )
                                for allocation in line.allocations
                            ),
                        )
                        for line in payload.lines
                    ),
                ),
            )
        except ValueError as error:
            session.rollback()
            raise HTTPException(status_code=409, detail=str(error)) from error
        if result.replayed:
            response.status_code = status.HTTP_200_OK
        return {"sessionId": result.session_id, "replayed": result.replayed}

    return api
