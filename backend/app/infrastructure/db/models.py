"""Minimal relational persistence for the Storage vertical slice."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class FoodDefinitionRow(Base):
    __tablename__ = "food_definitions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    names: Mapped[dict[str, str]] = mapped_column(JSON)
    aliases: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict)
    category: Mapped[str] = mapped_column(String(50), default="other")
    visual_key: Mapped[str] = mapped_column(String(100))
    base_unit: Mapped[str] = mapped_column(String(20))
    rounding_increment: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    package_presets: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    recommended_storage: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(20), default="SEEDED")
    active: Mapped[bool] = mapped_column(default=True)
    # Admin-uploaded custom icon as a sanitized data URI (SVG or PNG). Stored in
    # the database so deployments keep icons with the normal backup/restore flow.
    custom_icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ShelfLifeRuleRow(Base):
    __tablename__ = "shelf_life_rules"
    __table_args__ = (
        # One shelf-life default per food and storage location (DE-02).
        UniqueConstraint(
            "food_definition_id", "storage_location", name="uq_shelf_life_food_location"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    food_definition_id: Mapped[str] = mapped_column(ForeignKey("food_definitions.id"), index=True)
    storage_location: Mapped[str] = mapped_column(String(20))
    duration_days: Mapped[int] = mapped_column()
    source_note: Mapped[str | None] = mapped_column(String(200), nullable=True)


class AppSettingRow(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict[str, object]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class InventoryLotRow(Base):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_lot_quantity_non_negative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    food_definition_id: Mapped[str] = mapped_column(ForeignKey("food_definitions.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    storage_location: Mapped[str] = mapped_column(String(20), index=True)
    stored_on: Mapped[date] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_source: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class InventoryTransactionRow(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    lot_id: Mapped[str] = mapped_column(ForeignKey("inventory_lots.id"), index=True)
    cooking_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(40), index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    reversal_of: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # Base key (<=120) plus a per-lot ":<lotId>" suffix.
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ActivityEventRow(Base):
    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    food_definition_id: Mapped[str] = mapped_column(ForeignKey("food_definitions.id"), index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    display_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RescueSessionRow(Base):
    __tablename__ = "rescue_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="SEARCHED", index=True)
    selected_foods: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    servings: Mapped[int] = mapped_column()
    locale: Mapped[str] = mapped_column(String(10), default="en")
    cuisine: Mapped[str] = mapped_column(String(30), default="", server_default="")
    source_results: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    ai_plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ai_plan_error: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_analyses: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    searched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SavedRecipeRow(Base):
    __tablename__ = "saved_recipes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    base_yield: Mapped[int] = mapped_column()
    multiplier: Mapped[float | None] = mapped_column(nullable=True)
    ingredients: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    instructions: Mapped[list[str]] = mapped_column(JSON)
    origin_type: Mapped[str] = mapped_column(String(20), default="personal")
    origin_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_publisher: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_cooked_portion: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
