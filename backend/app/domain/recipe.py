"""Recipe amount rules (contracts DE-06, DE-07, section 6.2).

Base amounts are normalized recipe truth and never scale in place. Effective
amounts are derived as ``base_amount x portion_multiplier`` for NUMERIC
ingredients only; QUALITATIVE amounts (e.g. "to taste") never scale and UNKNOWN
amounts expose no number. Editing an effective amount back-normalizes the base
amount with the active multiplier. Internal precision stays in ``Decimal``;
rounding to the unit increment happens only for display.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.errors import InvalidMultiplierError
from app.domain.quantity import DecimalLike, _coerce_decimal, round_to_increment
from app.domain.types import IngredientAmountKind, IngredientMappingStatus

# Provenance values per DE-07.
PROVENANCE_SOURCE = "SOURCE"
PROVENANCE_AI_INFERENCE = "AI_INFERENCE"
PROVENANCE_USER_EDIT = "USER_EDIT"


@dataclass
class RecipeIngredient:
    """DE-07 RecipeIngredient (editor model; persistence mapping comes later)."""

    id: str
    display_name: str
    amount_kind: IngredientAmountKind
    food_definition_id: str | None = None
    storage_food_reference: str | None = None
    base_amount: Decimal | None = None
    unit: str | None = None
    qualitative_amount: str | None = None
    mapping_status: IngredientMappingStatus = IngredientMappingStatus.UNRESOLVED
    provenance: str = PROVENANCE_USER_EDIT
    needs_review: bool = False


def validate_multiplier(multiplier: DecimalLike) -> Decimal:
    """Portion multiplier must be a positive decimal (never a float)."""
    value = _coerce_decimal(multiplier)
    if value <= 0:
        raise InvalidMultiplierError("portion multiplier must be a positive decimal")
    return value


def effective_amount(ingredient: RecipeIngredient, multiplier: DecimalLike) -> Decimal | None:
    """``base_amount x portion_multiplier`` for NUMERIC ingredients.

    Returns ``None`` for QUALITATIVE and UNKNOWN ingredients: they have no
    scalable number. Never mutates ``base_amount``.
    """
    factor = validate_multiplier(multiplier)
    if ingredient.amount_kind is not IngredientAmountKind.NUMERIC:
        return None
    if ingredient.base_amount is None:
        raise ValueError("NUMERIC ingredient requires a base_amount")
    return _coerce_decimal(ingredient.base_amount) * factor


def back_normalize_base_amount(edited_effective: DecimalLike, multiplier: DecimalLike) -> Decimal:
    """Base amount implied by an effective amount edited at ``multiplier``.

    ``base = edited_effective / multiplier`` keeps the recipe coherent when the
    multiplier changes again afterwards.
    """
    factor = validate_multiplier(multiplier)
    value = _coerce_decimal(edited_effective)
    if value < 0:
        raise ValueError("edited effective amount must be non-negative")
    return value / factor


def display_amount(
    ingredient: RecipeIngredient,
    multiplier: DecimalLike,
    increment: Decimal,
) -> Decimal | None:
    """Effective amount rounded to the unit increment, for display only."""
    value = effective_amount(ingredient, multiplier)
    if value is None:
        return None
    return round_to_increment(value, increment)
