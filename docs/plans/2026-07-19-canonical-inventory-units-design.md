# Canonical Inventory Units Design

## Problem

Storage currently exposes a five-unit UI vocabulary, but the backend quantity table still accepts food-specific count aliases such as `head`, `clove`, and `bunch`. Existing demo databases can therefore continue to display `head` or `bulb`, and free-form unit fields can reintroduce them. The current quantity icon also resembles a weighing scale, so it cannot truthfully represent count and volume quantities.

## Approved Product Contract

- Storage accepts exactly five user-selectable units: `g`, `kg`, `ml`, `l`, and `piece`.
- Unit entry is always a dropdown; Storage never asks the user to type a unit string.
- A FoodDefinition retains one base unit. A later check-in may use a compatible unit from the same dimension, and the server converts the incoming amount into that base unit before persistence.
- `g` and `kg` convert exactly through a factor of 1000. `ml` and `l` convert exactly through a factor of 1000. `piece` has no implicit mass or volume conversion.
- Legacy count aliases `head`, `bulb`, `clove`, and `bunch` migrate to `piece` without changing the numeric quantity.
- New API writes reject food-specific count aliases and unknown units.
- A same-dimension base-unit edit converts every lot for the FoodDefinition transactionally before changing the shared base unit. Cross-dimension edits remain unavailable because Fridge Pal must not invent piece-weight or density conversions.
- The ambiguous quantity icon is removed. Quantity is communicated through the localized field label and a visually distinct numeric value capsule; time status retains its clock or tombstone icon.

## Data Flow

1. Add Food or Food Edit supplies a quantity plus a selected canonical unit.
2. The API validates the selected unit against the canonical Storage vocabulary.
3. For an existing FoodDefinition, the application service converts compatible input to the FoodDefinition base unit before creating or reducing lots.
4. For a same-dimension base-unit edit, the service converts all associated lot quantities and records the unit change in the existing auditable edit event.
5. Storage overview continues to aggregate lots in the FoodDefinition base unit.

## Error Handling

- Unknown or special units fail at the API boundary with a validation error.
- Cross-dimension changes fail visibly rather than guessing a conversion.
- Legacy normalization is idempotent and runs before demo seeding so an existing local database becomes canonical without duplicate lots.

## Verification

- Contract tests cover `kg → g`, `g → kg`, `l → ml`, `ml → l`, rejection of `head`, and idempotent legacy normalization.
- Mutation tests confirm a base-unit edit converts every lot and preserves aggregate physical quantity.
- Frontend checks cover dropdown-only unit entry and removal of the quantity icon.
- ESLint, vue-tsc, Vite build, backend Ruff/mypy, focused mutation tests, and a narrow browser inspection are required.
