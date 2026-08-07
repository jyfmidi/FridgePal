# Personal Food Isolation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make every newly created custom food private and reusable only by its creator while keeping seeded and Admin-created presets globally shared.

**Architecture:** Add one nullable indexed `owner_user_id` to the existing FoodDefinition row; `NULL` remains public and a user ID denotes personal ownership. Scope library and check-in reads at the application boundary, keep Admin operations public-only, and invalidate the frontend library cache on every authentication transition. No new table, review queue, or publishing workflow is introduced.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2, SQLite/MySQL-compatible additive startup migration, pytest, Vue 3, TypeScript, Playwright.

---

### Task 1: Add the ownership contract and additive schema migration

**Files:**
- Modify: `docs/PRODUCT_REQUIREMENTS.md`
- Modify: `docs/DOMAIN_AND_AI_CONTRACTS.md`
- Modify: `backend/app/infrastructure/db/models.py`
- Modify: `backend/app/infrastructure/db/session.py`
- Create: `backend/tests/integration/test_personal_food_schema.py`

**Step 1: Write the failing schema tests**

Assert that a fresh `FoodDefinitionRow` schema has nullable `owner_user_id`, a foreign key to `users.id`, and an index. Create a legacy SQLite `food_definitions` table without the column, call `create_database`, and assert the additive migration creates the nullable column and index without changing existing rows.

**Step 2: Run the schema test and verify RED**

```bash
cd backend
PYTHONPATH=. /Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m pytest \
  tests/integration/test_personal_food_schema.py -q
```

Expected: FAIL because `owner_user_id` and its index do not exist.

**Step 3: Implement the minimal schema change**

Add:

```python
owner_user_id: Mapped[str | None] = mapped_column(
    ForeignKey("users.id"), nullable=True, index=True
)
```

Extend `_ensure_columns` with an additive nullable `VARCHAR(36)` column and an idempotent owner index for pre-existing databases. Existing rows remain public through `NULL`; do not guess legacy ownership.

Update `FR-LIB-003`, `FR-ADM-005`, `DE-01`, and the security/privacy contract to state that public definitions have no owner and personal definitions are user-scoped.

**Step 4: Run the schema tests and verify GREEN**

Expected: PASS on both fresh and legacy SQLite schemas.

**Step 5: Create a temporary checkpoint commit**

```bash
git add docs/PRODUCT_REQUIREMENTS.md docs/DOMAIN_AND_AI_CONTRACTS.md \
  backend/app/infrastructure/db/models.py backend/app/infrastructure/db/session.py \
  backend/tests/integration/test_personal_food_schema.py
git commit -m "feat(food-library): 增加个人食材所有权字段"
```

### Task 2: Scope custom creation and Food Library reads by user

**Files:**
- Modify: `backend/app/application/inventory/service.py`
- Modify: `backend/app/application/admin/service.py`
- Modify: `backend/app/api/inventory.py`
- Modify: `backend/tests/integration/test_isolation.py`
- Modify: `backend/tests/integration/test_inventory_api.py`
- Modify: `backend/tests/integration/test_auth_api.py`

**Step 1: Write failing isolation contracts**

Cover these behaviors through authenticated API clients:

1. Alice and Bob create the same `custom:<slug>` and receive different persisted FoodDefinition IDs through Storage.
2. Alice's `/api/library` contains only Alice's personal definition plus public presets; Bob receives only Bob's equivalent plus public presets.
3. A crafted check-in using another user's persisted personal ID returns 404 and creates no lot or ActivityEvent.
4. Repeated same-user creation reuses the same personal definition and preserves base-unit conversion.
5. Seeded definitions remain visible to both users.

**Step 2: Run focused tests and verify RED**

```bash
cd backend
PYTHONPATH=. /Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m pytest \
  tests/integration/test_isolation.py \
  tests/integration/test_inventory_api.py \
  tests/integration/test_auth_api.py -q
```

Expected: FAIL because custom definitions are globally keyed and `list_library` is not user-scoped.

**Step 3: Implement stable personal IDs and access checks**

Derive new personal IDs with UUID5 from `user_id` plus the client custom key. Store the temporary `custom:<slug>` as `visual_key` for deterministic monogram rendering. Create the definition with `owner_user_id=user_id` inside the existing check-in transaction.

For an existing definition, allow it only when:

```text
food.active AND (food.owner_user_id IS NULL OR food.owner_user_id == user_id)
```

Return a stable 404 response for foreign or inactive definitions. Keep idempotent replay ahead of definition resolution.

Change `list_library(session, user_id)` to filter:

```python
FoodDefinitionRow.active.is_(True),
or_(FoodDefinitionRow.owner_user_id.is_(None), FoodDefinitionRow.owner_user_id == user_id)
```

Pass the authenticated user ID from `/api/library`.

**Step 4: Run focused tests and verify GREEN**

Expected: PASS with distinct same-name IDs and zero cross-user disclosure.

**Step 5: Create a temporary checkpoint commit**

```bash
git add backend/app/application/inventory/service.py \
  backend/app/application/admin/service.py backend/app/api/inventory.py \
  backend/tests/integration/test_isolation.py \
  backend/tests/integration/test_inventory_api.py \
  backend/tests/integration/test_auth_api.py
git commit -m "feat(food-library): 隔离用户个人食材"
```

### Task 3: Keep personal foods outside every Admin operation

**Files:**
- Modify: `backend/app/application/admin/service.py`
- Modify: `backend/tests/integration/test_admin_api.py`

**Step 1: Write failing Admin privacy tests**

Create a personal food through a regular-user check-in, then authenticate as Admin. Assert:

- Admin list omits the personal ID and name.
- Admin update, soft-delete, icon upload, and icon removal return `ADMIN_FOOD_NOT_FOUND`/404 for the personal ID.
- Admin-created definitions explicitly remain public and appear in another user's library.

**Step 2: Run the Admin test and verify RED**

```bash
cd backend
PYTHONPATH=. /Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m pytest \
  tests/integration/test_admin_api.py -q
```

Expected: FAIL because Admin currently lists and mutates every FoodDefinition.

**Step 3: Implement public-only Admin helpers**

Filter `list_food_definitions` by `owner_user_id IS NULL`. Add one internal public-definition lookup used by update, delete, icon upload, and icon removal; it returns the existing stable not-found error for personal IDs. Set `owner_user_id=None` explicitly on Admin creation.

Do not add a personal-food panel, publish button, or moderation state.

**Step 4: Run the Admin and isolation tests and verify GREEN**

Expected: PASS.

**Step 5: Create a temporary checkpoint commit**

```bash
git add backend/app/application/admin/service.py \
  backend/tests/integration/test_admin_api.py
git commit -m "fix(admin): 隐藏并拒绝操作个人食材"
```

### Task 4: Prevent frontend Food Library cache leakage across accounts

**Files:**
- Modify: `frontend/src/features/storage/libraryStore.ts`
- Modify: `frontend/src/features/auth/authStore.ts`
- Create: `e2e/tests/personal-food-isolation.spec.ts`

**Step 1: Write the failing browser contract**

In one browser session:

1. Register Alice, create and save a uniquely named personal food, then confirm it appears in Alice's Add Food suggestions.
2. Log Alice out and register Bob.
3. Search the same name and assert Alice's personal suggestion is absent while the create-custom action is available.
4. Create Bob's same-named food and confirm Bob can reuse only his own definition.

Run this contract under both configured mobile and desktop projects.

**Step 2: Run Playwright and verify RED**

```bash
cd e2e
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  node_modules/@playwright/test/cli.js test tests/personal-food-isolation.spec.ts \
  --config playwright.config.ts
```

Expected: FAIL because the module-level library cache survives logout/account switching.

**Step 3: Implement generation-guarded cache reset**

Export `resetFoodLibrary()` from `libraryStore.ts`. It increments a generation token, clears `serverFoods`, resets `loaded`, and detaches the current shared load. A response may update state only when its captured generation still matches.

Call the reset after successful login and registration and in the `finally` branch of logout. Do not clear the built-in static catalog.

**Step 4: Run frontend checks and browser tests and verify GREEN**

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

Then run the focused Playwright contract. Expected: all PASS.

**Step 5: Create a temporary checkpoint commit**

```bash
git add frontend/src/features/storage/libraryStore.ts \
  frontend/src/features/auth/authStore.ts \
  e2e/tests/personal-food-isolation.spec.ts
git commit -m "fix(auth): 切换账号时清除个人食材缓存"
```

### Task 5: Release verification and outcome-oriented history

**Files:**
- Modify if necessary: `docs/IMPLEMENTATION_PLAN.md`
- Verify: all changed files

**Step 1: Run backend release checks**

```bash
cd backend
PYTHONPATH=. /Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m pytest -q
/Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m ruff check app tests
/Users/jyfmidi/Dev/Frigital/backend/.venv/bin/python -m mypy app
```

Expected: all PASS.

**Step 2: Run frontend and browser release checks**

Run ESLint, vue-tsc, production build, and the complete mobile/desktop Playwright suite. Confirm Add Food, Admin, authentication, and existing 70-food preset coverage remain green.

**Step 3: Verify database-facing behavior**

Start an isolated SQLite app, create two users with the same custom food name, and confirm distinct FoodDefinition IDs and scoped libraries. Confirm Admin still lists exactly the public definitions and Storage/History remain user-isolated.

**Step 4: Inspect the final diff and canonical contracts**

```bash
git diff --check
git status --short
```

Confirm no new table, moderation workflow, publishing UI, or unrelated file entered the change.

**Step 5: Squash temporary checkpoints into one searchable Chinese commit**

Preserve the verified final tree and consolidate this plan's temporary commits into:

```text
feat(food-library): 隔离用户个人食材
```

The commit body should mention user-scoped definitions, Admin exclusion, deterministic collision-free IDs, authentication cache invalidation, schema migration, and full regression coverage.
