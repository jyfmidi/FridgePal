"""Canonical enums from docs/DOMAIN_AND_AI_CONTRACTS.md section 2.

Values are persisted as these exact strings; do not rename members or values.
"""

from enum import StrEnum


class StorageLocation(StrEnum):
    FRIDGE = "FRIDGE"
    FREEZER = "FREEZER"
    PANTRY = "PANTRY"


class InventoryLotStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEPLETED = "DEPLETED"
    DISCARDED = "DISCARDED"


class ExpirySource(StrEnum):
    LIBRARY_DEFAULT = "LIBRARY_DEFAULT"
    USER_OVERRIDE = "USER_OVERRIDE"
    NONE = "NONE"


class FoodOrigin(StrEnum):
    SEEDED = "SEEDED"
    USER_CREATED = "USER_CREATED"


class RescueSessionStatus(StrEnum):
    DRAFT = "DRAFT"
    SEARCHING = "SEARCHING"
    SEARCHED = "SEARCHED"
    PLAN_READY = "PLAN_READY"
    COOKED = "COOKED"
    ARCHIVED = "ARCHIVED"


class RecipeOriginType(StrEnum):
    AI_PLAN = "AI_PLAN"
    WEB_SOURCE = "WEB_SOURCE"
    SAVED_RECIPE = "SAVED_RECIPE"
    PERSONAL = "PERSONAL"


class RecipeAnalysisStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    READY = "READY"
    FAILED = "FAILED"


class IngredientAmountKind(StrEnum):
    NUMERIC = "NUMERIC"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


class IngredientMappingStatus(StrEnum):
    EXACT = "EXACT"
    ALIAS = "ALIAS"
    SUGGESTED = "SUGGESTED"
    UNRESOLVED = "UNRESOLVED"


class CookingSessionStatus(StrEnum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"


class InventoryReason(StrEnum):
    CHECK_IN = "CHECK_IN"
    EDIT = "EDIT"
    MANUAL_CONSUMPTION = "MANUAL_CONSUMPTION"
    COOKING = "COOKING"
    DISCARD = "DISCARD"
    MOVE = "MOVE"
    REVERSAL = "REVERSAL"
