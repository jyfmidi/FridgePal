# Seeded Food Library Design

## Goal

Populate the shared preset database with the 70 approved fresh household foods represented by the curated Food Token library. Every preset remains editable in Admin and available to all users through Add Food, while no preset operation creates or mutates user inventory.

## Scope

The catalog includes the 70 approved keys in `2026-08-01-common-food-icon-library-design.md`: 38 vegetables, fungi, and aromatics; 18 fruits; 10 meat, egg, and aquatic foods; and 4 soy or chilled foods. Compatibility-only `rice` and `pasta` remain valid visual keys and inactive seeded definitions for the existing demo inventory, but they are not part of this active fresh-food catalog.

Each preset contains:

- stable lowercase kebab-case food key;
- English and Simplified Chinese display names;
- useful English and Simplified Chinese search aliases;
- category;
- curated visual key;
- canonical base unit and rounding increment;
- one or two common quantity presets;
- recommended storage location;
- one conservative shelf-life rule for that recommended location;
- a source note that identifies the rule as an editable starter estimate.

## Architecture

Add an immutable typed catalog manifest under backend infrastructure and a dedicated `seed_food_library()` application-startup operation. Food Library seeding runs independently of demo-account and demo-inventory seeding, including when `SEED_DEMO_DATA=false`.

The manifest is server-owned database seed data. The frontend continues to receive the active library through `/api/library`; its existing server-to-catalog mapping and visual-key registry require no new parallel data path.

## Upgrade and ownership policy

Use an `AppSettingRow` seed-version marker so each catalog version is applied once per database. A normal database contains 70 active preset definitions; demo-enabled databases also contain the two inactive compatibility definitions for `rice` and `pasta`.

For a missing food key, insert the complete seeded definition and its shelf-life rule. For an existing row, preserve names, visual key, base unit, recommended storage, active state, custom icon, and every non-empty Admin-managed field. Fill only legacy seed gaps such as the default `other` category, empty aliases, empty package presets, a missing rounding increment, or a missing recommended-location shelf-life rule.

The upgrade never reactivates a soft-deleted food and never changes a user-created definition. After the version marker is written, normal restarts perform no catalog mutation. A future catalog revision must increment the version and define another explicit, non-destructive upgrade.

## Shelf-life policy

Shelf-life values generate a suggested use-by date and Use Soon reminder; they are not a food-safety guarantee. Use one refrigerated day for generic raw pork, beef, lamb, poultry, and fish because an unspecific definition may include minced or otherwise highly perishable cuts. Use three days for shrimp, one for crab, and 21 for shell eggs. For produce, use short quality-oriented starter estimates based on the recommended storage class: leafy greens, mushrooms, and fresh beans are refrigerated; cold-sensitive tropical fruit is kept in Pantry.

Every rule receives a source note such as `Fridge Pal conservative starter estimate; inspect freshness and packaging; editable in Admin.` More specific protein notes may cite the FoodSafety.gov cold-storage guidance. Prepackaged milk and yogurt remain subordinate to their printed use-by and storage instructions.

## Quantity and unit policy

Use only canonical units: `g`, `kg`, `ml`, `l`, and `piece`. Prefer grams for produce sold or consumed by variable mass; use pieces when household counting is natural and stable; use milliliters for milk. Package presets are quick-fill conveniences, not package-size claims, and stay within the base unit's compatible dimension.

The existing frontend currently initializes server-only foods at quantity `1`; Add Food should instead use the first package preset as the initial quantity when one is available. This makes the newly seeded library useful without expanding the database schema.

## Failure and transaction behavior

Apply the complete catalog version in one database transaction. Validation or persistence failure rolls back all changes and leaves the version marker untouched. Duplicate execution is idempotent. Shelf-life uniqueness remains one rule per food and storage location.

## Verification

- Contract-test the exact 70-key manifest and required bilingual/basic fields.
- Verify fresh-database insertion, legacy 16-row enrichment, preservation of Admin edits and inactive state, and idempotent repeat execution.
- Verify seeding occurs when demo data is disabled and creates no inventory lots or activity events.
- Verify `/api/library` returns all 70 active presets and Add Food uses each entry's first package preset as its initial quantity.
- Run backend unit/integration checks, frontend lint/typecheck/build, and mobile/desktop Admin/Add Food browser coverage.
