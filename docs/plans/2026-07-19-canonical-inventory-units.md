# Canonical Inventory Units Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restrict Storage to five selectable units, convert compatible mass/volume writes exactly, normalize legacy count aliases, and remove the ambiguous quantity icon.

**Architecture:** Keep one base unit on each FoodDefinition. Validate canonical Storage units at HTTP boundaries, use the existing Decimal quantity conversion domain for compatible writes, and normalize legacy database aliases before demo seeding. Frontend unit fields become dropdowns derived from the current unit dimension.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy, pytest, Vue 3, TypeScript, vue-i18n.

---

### Task 1: Lock the Storage unit contract with failing tests

**Files:**
- Modify: `backend/tests/integration/test_mutations_api.py`
- Modify: `backend/tests/integration/test_inventory_api.py`

1. Add a check-in test proving `0.5 kg` is persisted as `500 g` when the FoodDefinition base unit is `g`.
2. Add the inverse mass test and both `l`/`ml` volume directions.
3. Add an API-boundary test proving `head` is rejected.
4. Add a multi-lot edit test proving a same-dimension base-unit change converts every lot.
5. Add a legacy-normalization test for `head`, `bulb`, `clove`, and `bunch` to `piece`.
6. Run the focused tests and confirm they fail for the missing contract.

### Task 2: Implement canonical validation and exact conversion

**Files:**
- Create: `backend/app/domain/inventory_unit.py`
- Modify: `backend/app/api/inventory.py`
- Modify: `backend/app/application/inventory/service.py`

1. Define the canonical Storage vocabulary and legacy alias mapping.
2. Validate check-in, edit, reduce, and cooking mutation units at the API boundary.
3. Convert compatible check-in quantities into the existing FoodDefinition base unit with Decimal arithmetic.
4. Convert all FoodDefinition lots transactionally during a same-dimension base-unit edit.
5. Reject cross-dimension changes without explicit conversion metadata.
6. Run the focused tests and confirm they pass.

### Task 3: Normalize existing local databases

**Files:**
- Modify: `backend/app/infrastructure/db/demo_seed.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/integration/test_inventory_api.py`

1. Add an idempotent legacy-unit normalization function.
2. Run it before demo seeding during application startup.
3. Preserve numeric quantities while mapping legacy count aliases to `piece`.
4. Verify repeated startup makes no further changes or duplicate data.

### Task 4: Make all unit entry dropdown-only

**Files:**
- Modify: `frontend/src/features/storage/inventory.ts`
- Modify: `frontend/src/views/AddFoodView.vue`
- Modify: `frontend/src/views/StorageItemView.vue`
- Modify: `frontend/src/i18n/index.ts`

1. Centralize canonical unit lists and compatible-unit helpers in the Storage feature.
2. Replace custom-food and Food Edit free-text unit inputs with selects.
3. Limit existing foods to units compatible with their current dimension; allow all five when defining a new custom food.
4. Keep quantity as a direct numeric input and show a clear error for incompatible server responses.

### Task 5: Remove the ambiguous quantity icon

**Files:**
- Modify: `frontend/src/components/storage-tile/StorageTile.vue`
- Modify: `frontend/src/views/StorageItemView.vue`
- Modify: `frontend/src/components/AppIcon.vue`

1. Remove the scale-like icon from Storage quantity capsules and field labels.
2. Retain the visually distinct value capsule and localized `Quantity` label.
3. Remove the unused icon definition after a residue search confirms no consumers remain.

### Task 6: Update canonical contracts and verify

**Files:**
- Modify: `docs/PRODUCT_REQUIREMENTS.md`
- Modify: `docs/DOMAIN_AND_AI_CONTRACTS.md`
- Modify: `docs/UX_SPEC.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

1. Document the five-unit Storage vocabulary and exact compatible conversions.
2. Run focused backend contract tests, Ruff, and mypy.
3. Run frontend ESLint, vue-tsc, and Vite production build.
4. Run `git diff --check` and search for special-unit or quantity-icon residue.
5. Inspect Add Food, Food Edit, and Storage at the representative narrow viewport.
