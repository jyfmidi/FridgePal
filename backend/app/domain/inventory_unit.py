"""Canonical unit vocabulary for persisted Storage quantities."""

CANONICAL_INVENTORY_UNITS = frozenset({"g", "kg", "ml", "l", "piece"})
LEGACY_COUNT_UNIT_ALIASES = frozenset({"head", "bulb", "clove", "bunch"})


def canonical_inventory_unit(value: str) -> str:
    """Return a normalized canonical Storage unit or reject the value."""
    normalized = value.strip().lower()
    if normalized not in CANONICAL_INVENTORY_UNITS:
        allowed = ", ".join(sorted(CANONICAL_INVENTORY_UNITS))
        raise ValueError(f"unit must be one of: {allowed}")
    return normalized
