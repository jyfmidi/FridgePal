# Seeded Food Library Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Seed the approved 70-food bilingual preset catalog into the shared database without touching user inventory or overwriting Admin-owned changes.

**Architecture:** Define one immutable, typed backend catalog and apply it through a versioned transactional startup seed independent of demo inventory. The existing `/api/library` and Admin flows remain the only client data path; Add Food uses the first package preset as the initial quantity for server-provided foods.

**Tech Stack:** Python 3.11+, SQLAlchemy 2, FastAPI, pytest, Vue 3, TypeScript, Playwright.

---

### Task 1: Define and validate the 70-food catalog

**Files:**
- Create: `backend/app/infrastructure/db/food_library_catalog.py`
- Create: `backend/tests/unit/infrastructure/test_food_library_catalog.py`

**Step 1: Write the failing catalog contract**

Define the exact expected key set from `docs/plans/2026-08-01-common-food-icon-library-design.md`. Assert:

```python
assert len(FOOD_LIBRARY_CATALOG) == 70
assert {food.food_key for food in FOOD_LIBRARY_CATALOG} == EXPECTED_KEYS
assert "rice" not in EXPECTED_KEYS
assert "pasta" not in EXPECTED_KEYS
```

For every entry, require English and `zh-CN` names, aliases for both locales, one of the approved category keys, `visual_key == food_key`, a canonical unit, positive rounding increment, one or two positive compatible package presets, a recommended storage location, and exactly one positive conservative shelf-life rule for that location.

**Step 2: Run the unit test and verify RED**

Run from `backend/`:

```bash
.venv/bin/pytest tests/unit/infrastructure/test_food_library_catalog.py -q
```

Expected: collection fails because `food_library_catalog` does not exist.

**Step 3: Add the typed manifest**

Use frozen dataclasses for `PresetQuantity`, `PresetShelfLife`, and `PresetFood`. Add the 70 approved entries grouped as vegetables/fungi/aromatics, fruit, meat/egg/aquatic, and soy/chilled.

Use only `g`, `kg`, `ml`, `l`, and `piece`. Prefer a mass base unit for variable-size produce and meat, `piece` for naturally counted fruit and eggs, and `ml` for milk. Use category keys `vegetable`, `fruit`, `meat`, `egg`, `aquatic`, `soy`, and `dairy`.

Set conservative recommended-location rules. Generic raw pork, beef, lamb, poultry, and fish use one refrigerated day because the definition may include minced or otherwise highly perishable cuts; shrimp uses three; crab uses one; shell eggs use 21. Packaged milk/yogurt and all produce rules carry an editable starter-estimate source note and remain subordinate to printed packaging and observed freshness.

**Step 4: Run the unit test and verify GREEN**

Expected: PASS with exactly 70 valid entries.

**Step 5: Commit**

```bash
git add backend/app/infrastructure/db/food_library_catalog.py \
  backend/tests/unit/infrastructure/test_food_library_catalog.py
git commit -m "feat: define seeded Food Library catalog"
```

### Task 2: Add versioned, non-destructive database seeding

**Files:**
- Create: `backend/app/infrastructure/db/food_library_seed.py`
- Create: `backend/tests/integration/test_food_library_seed.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing integration contracts**

Cover these behaviors against a fresh foreign-key-enabled SQLite database:

1. One call inserts 70 `FoodDefinitionRow` records, 70 recommended-location `ShelfLifeRuleRow` records, and one version marker.
2. It creates zero `InventoryLotRow` and zero `ActivityEventRow` records.
3. A second call is idempotent.
4. A legacy seeded row is enriched only where its category is `other`, aliases/presets are empty, rounding increment is null, or its recommended-location rule is absent.
5. Existing names, visual key, base unit, recommended storage, custom icon, active false state, non-empty fields, existing rules, and every `USER_CREATED` row are preserved.
6. An injected persistence failure rolls back both catalog changes and the version marker.

**Step 2: Run the integration test and verify RED**

```bash
.venv/bin/pytest tests/integration/test_food_library_seed.py -q
```

Expected: FAIL because `seed_food_library` does not exist.

**Step 3: Implement one transactional catalog version**

Add `FOOD_LIBRARY_SEED_VERSION = 1` and marker key `food_library_seed_version`. The operation accepts a `sessionmaker`, opens one session/transaction, returns immediately when the marker is current, inserts missing rows, and fills only approved gaps on existing `SEEDED` rows. Create a shelf-life rule only when the recommended-location pair is absent. Write the marker last inside the same transaction.

Do not call Admin create/update functions because they commit per food. Do not catch persistence errors inside the transaction.

**Step 4: Wire startup independently of demo data**

Call `seed_food_library(session_factory)` after database creation and legacy-unit normalization, before the `if settings.seed_demo_data` branch. This guarantees that production deployments with demo seeding disabled still receive presets.

**Step 5: Run the integration test and verify GREEN**

Expected: PASS.

**Step 6: Commit**

```bash
git add backend/app/infrastructure/db/food_library_seed.py \
  backend/tests/integration/test_food_library_seed.py backend/app/main.py
git commit -m "feat: seed shared Food Library at startup"
```

### Task 3: Reconcile demo seeding and API behavior

**Files:**
- Modify: `backend/app/infrastructure/db/demo_seed.py`
- Modify: `backend/tests/integration/test_demo_seed.py`
- Modify: `backend/tests/integration/test_auth_api.py`
- Modify: `backend/tests/integration/test_admin_api.py`

**Step 1: Write the failing deployment-facing expectations**

- Update the demo-seed contract to expect 70 active shared presets plus inactive `rice` and `pasta` compatibility definitions, but only the existing 16 demo lots/events.
- Extend `test_seed_demo_data_false_skips_demo_user_and_register_seed` to register a user, assert empty Storage, then assert `/api/library` returns exactly 70 active presets including `bok-choy`, `dragon-fruit`, and `lamb`.
- Extend the Admin list contract to assert the seeded entries carry bilingual names, category, aliases, presets, visual key, recommended storage, and source-noted shelf life.

**Step 2: Run the focused tests and verify RED**

```bash
.venv/bin/pytest tests/integration/test_demo_seed.py \
  tests/integration/test_auth_api.py::test_seed_demo_data_false_skips_demo_user_and_register_seed \
  tests/integration/test_admin_api.py -q
```

Expected: FAIL until startup seeding and demo-row reuse are fully reconciled.

**Step 3: Reuse catalog definitions in demo inventory**

Keep `DEMO_FOODS` as the 16-lot demonstration fixture. When a definition is unexpectedly absent, construct the 14 catalog-backed foods from their full catalog entries. Construct `rice` and `pasta` as explicit inactive compatibility definitions. Preserve current demo quantities, urgency dates, idempotency keys, and user-scoped lots/events.

**Step 4: Run the focused tests and verify GREEN**

Expected: PASS with 70 shared presets and 16 demo lots/events.

**Step 5: Commit**

```bash
git add backend/app/infrastructure/db/demo_seed.py \
  backend/tests/integration/test_demo_seed.py \
  backend/tests/integration/test_auth_api.py \
  backend/tests/integration/test_admin_api.py
git commit -m "test: cover complete seeded Food Library"
```

### Task 4: Use package presets as Add Food defaults

**Files:**
- Modify: `frontend/src/features/storage/libraryStore.ts`
- Create: `e2e/tests/food-library-presets.spec.ts`

**Step 1: Write the failing browser contract**

Sign in a fresh user, open Add Food, search for a server-only preset such as Bok choy, select it, and assert the quantity/unit/location and suggested expiration are populated from the server definition. Assert the Food Token is the curated `bok-choy` SVG rather than a monogram.

**Step 2: Run desktop Playwright and verify RED**

```bash
cd e2e
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  node_modules/@playwright/test/cli.js test tests/food-library-presets.spec.ts \
  --project desktop-chrome --config playwright.config.ts
```

Expected: FAIL because server-only foods currently initialize as `1 <baseUnit>`.

**Step 3: Implement the first-preset default**

In `toCatalogItem`, compute the normalized package presets once. When at least one exists, set `defaultQuantity` and `defaultUnit` from the first preset; otherwise retain `1` and the base unit. Keep all preset chips available.

**Step 4: Run focused frontend checks and verify GREEN**

Run ESLint, vue-tsc, and the focused Playwright contract. Expected: PASS.

**Step 5: Commit**

```bash
git add frontend/src/features/storage/libraryStore.ts e2e/tests/food-library-presets.spec.ts
git commit -m "fix: apply Food Library quantity defaults"
```

### Task 5: Update canonical documentation and run the release gate

**Files:**
- Modify: `docs/PRODUCT_REQUIREMENTS.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify if necessary: `docs/DEPLOYMENT.md`

**Step 1: Update the owning decisions**

Resolve `OQ-04` to the approved 70-food bilingual fresh-food catalog, versioned non-destructive database seeding, and compatibility-only rice/pasta keys. Update Task 2's obsolete seven-food/import-file wording to the implemented manifest path and verification behavior.

**Step 2: Run backend verification**

Run all backend pytest tests, Ruff, and mypy. Expected: all PASS.

**Step 3: Run frontend and browser verification**

Run frontend ESLint, vue-tsc, Vite production build, `git diff --check`, and the complete Playwright mobile/desktop suite. Expected: all PASS.

**Step 4: Verify the real database-facing surface**

Start the isolated application database, confirm Admin lists 70 active presets and Add Food searches representative vegetable, fruit, protein, aquatic, and chilled entries. Confirm Storage remains empty for a new user when demo seeding is disabled.

**Step 5: Commit**

```bash
git add docs/PRODUCT_REQUIREMENTS.md docs/IMPLEMENTATION_PLAN.md docs/DEPLOYMENT.md
git commit -m "docs: record complete Food Library seed"
```
