"""Recipe amount scaling, qualitative handling, and back-normalization (contracts DE-06/DE-07)."""

from decimal import Decimal

import pytest
from app.domain.errors import InvalidMultiplierError
from app.domain.recipe import (
    RecipeIngredient,
    back_normalize_base_amount,
    display_amount,
    effective_amount,
    validate_multiplier,
)
from app.domain.types import IngredientAmountKind, IngredientMappingStatus


def numeric_ingredient(base_amount: str, unit: str = "g") -> RecipeIngredient:
    return RecipeIngredient(
        id="ing-1",
        display_name="Flour",
        food_definition_id="food-flour",
        amount_kind=IngredientAmountKind.NUMERIC,
        base_amount=Decimal(base_amount),
        unit=unit,
        mapping_status=IngredientMappingStatus.EXACT,
    )


def qualitative_ingredient() -> RecipeIngredient:
    return RecipeIngredient(
        id="ing-2",
        display_name="Salt",
        amount_kind=IngredientAmountKind.QUALITATIVE,
        qualitative_amount="to taste",
        mapping_status=IngredientMappingStatus.UNRESOLVED,
    )


def unknown_ingredient() -> RecipeIngredient:
    return RecipeIngredient(
        id="ing-3",
        display_name="Mystery spice",
        amount_kind=IngredientAmountKind.UNKNOWN,
        mapping_status=IngredientMappingStatus.UNRESOLVED,
        needs_review=True,
    )


class TestMultiplierValidation:
    def test_positive_multipliers_accepted(self) -> None:
        assert validate_multiplier(Decimal("0.5")) == Decimal("0.5")
        assert validate_multiplier(Decimal("1")) == Decimal("1")
        assert validate_multiplier(Decimal("2.75")) == Decimal("2.75")

    @pytest.mark.parametrize("bad", ["0", "-1", "-0.5"])
    def test_non_positive_multipliers_rejected(self, bad: str) -> None:
        with pytest.raises(InvalidMultiplierError):
            validate_multiplier(Decimal(bad))

    def test_float_multiplier_rejected(self) -> None:
        with pytest.raises(TypeError):
            validate_multiplier(0.5)  # type: ignore[arg-type]


class TestEffectiveAmount:
    def test_numeric_scales_linearly(self) -> None:
        ingredient = numeric_ingredient("200")
        assert effective_amount(ingredient, Decimal("0.5")) == Decimal("100")
        assert effective_amount(ingredient, Decimal("1")) == Decimal("200")
        assert effective_amount(ingredient, Decimal("2.5")) == Decimal("500.0")

    def test_base_amount_is_never_mutated_by_scaling(self) -> None:
        ingredient = numeric_ingredient("200")
        effective_amount(ingredient, Decimal("0.5"))
        assert ingredient.base_amount == Decimal("200")

    def test_qualitative_never_scales(self) -> None:
        ingredient = qualitative_ingredient()
        for multiplier in (Decimal("0.5"), Decimal("1"), Decimal("4")):
            assert effective_amount(ingredient, multiplier) is None
        assert ingredient.qualitative_amount == "to taste"

    def test_unknown_has_no_effective_amount(self) -> None:
        assert effective_amount(unknown_ingredient(), Decimal("2")) is None

    def test_numeric_without_base_amount_is_invalid(self) -> None:
        ingredient = numeric_ingredient("1")
        ingredient.base_amount = None
        with pytest.raises(ValueError):
            effective_amount(ingredient, Decimal("1"))

    def test_effective_amount_uses_exact_decimal(self) -> None:
        ingredient = numeric_ingredient("100")
        result = effective_amount(ingredient, Decimal("0.333"))
        assert result == Decimal("33.300")


class TestBackNormalization:
    def test_edited_effective_back_normalizes_base(self) -> None:
        # At multiplier 0.5 the user edits the effective amount to 150 g;
        # the stored base must become 300 g.
        assert back_normalize_base_amount(Decimal("150"), Decimal("0.5")) == Decimal("300")

    def test_back_normalization_at_multiplier_one(self) -> None:
        assert back_normalize_base_amount(Decimal("150"), Decimal("1")) == Decimal("150")

    def test_back_normalization_rejects_invalid_multiplier(self) -> None:
        with pytest.raises(InvalidMultiplierError):
            back_normalize_base_amount(Decimal("150"), Decimal("0"))

    def test_back_normalization_rejects_negative_amount(self) -> None:
        with pytest.raises(ValueError):
            back_normalize_base_amount(Decimal("-1"), Decimal("1"))

    def test_coherence_across_repeated_multiplier_changes(self) -> None:
        # Editing at multiplier m1 then viewing at m2 must behave as if the
        # edited effective amount itself scaled by m2/m1.
        edited_effective = Decimal("150")
        m1 = Decimal("0.5")
        ingredient = numeric_ingredient("200")
        ingredient.base_amount = back_normalize_base_amount(edited_effective, m1)
        for m2 in (Decimal("0.25"), Decimal("1"), Decimal("1.5"), Decimal("3")):
            assert effective_amount(ingredient, m2) == edited_effective * (m2 / m1)

    def test_generated_coherence_cases(self) -> None:
        # Property-style: base -> effective -> back-normalized is a fixed point.
        multipliers = [
            Decimal("0.25"),
            Decimal("0.5"),
            Decimal("0.75"),
            Decimal("1"),
            Decimal("1.5"),
            Decimal("2"),
            Decimal("3"),
        ]
        bases = [Decimal("0.1"), Decimal("2.5"), Decimal("33.333"), Decimal("1000")]
        for base in bases:
            for m in multipliers:
                ingredient = numeric_ingredient(str(base))
                eff = effective_amount(ingredient, m)
                assert eff is not None
                recovered = back_normalize_base_amount(eff, m)
                assert recovered == base


class TestDisplayRounding:
    def test_display_rounds_effective_to_increment(self) -> None:
        ingredient = numeric_ingredient("100")
        # effective = 33.3 at multiplier 0.333; display at 5 g increment -> 35
        assert display_amount(ingredient, Decimal("0.333"), Decimal("5")) == Decimal("35")

    def test_display_rounding_does_not_touch_internal_value(self) -> None:
        ingredient = numeric_ingredient("100")
        display_amount(ingredient, Decimal("0.333"), Decimal("5"))
        assert ingredient.base_amount == Decimal("100")
        assert effective_amount(ingredient, Decimal("0.333")) == Decimal("33.300")

    def test_display_of_non_numeric_is_none(self) -> None:
        assert display_amount(qualitative_ingredient(), Decimal("2"), Decimal("5")) is None
        assert display_amount(unknown_ingredient(), Decimal("2"), Decimal("5")) is None

    def test_repeated_portion_changes_do_not_accumulate_rounding_error(self) -> None:
        # Display rounding is applied to a snapshot only; base stays exact.
        ingredient = numeric_ingredient("10")
        increment = Decimal("5")
        seen = set()
        for multiplier in (Decimal("0.333"), Decimal("0.666"), Decimal("1"), Decimal("2")):
            seen.add(display_amount(ingredient, multiplier, increment))
            assert ingredient.base_amount == Decimal("10")
        # 3.33 -> 5, 6.66 -> 5, 10 -> 10, 20 -> 20 (all at a 5 g increment)
        assert seen == {Decimal("5"), Decimal("10"), Decimal("20")}
