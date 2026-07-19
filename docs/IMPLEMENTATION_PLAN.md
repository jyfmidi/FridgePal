# Fridgital Hackathon MVP Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task after Task 0 closes the stack decisions.

**Goal:** Build the P0 Fridgital golden loop as a private, responsive, Docker Compose-deployed single-user web application.

**Architecture:** Use one deployable application service with a responsive web client, domain/application modules, relational persistence, and server-only provider adapters. Keep inventory rules and AI/provider boundaries independent from the chosen web framework.

**Tech Stack:** `OQ-01` is resolved (user-selected): Vue 3 + Vite + TypeScript responsive client; FastAPI (Python 3.11+) application service; SQLAlchemy 2 + Alembic migrations; MySQL 8 in Docker Compose deployment, SQLite for local unit/integration tests; pytest (unit/integration/contract/security) and Playwright (browser E2E); vue-i18n for English/简体中文. `OQ-02` is resolved: retrieval uses a deterministic curated fixture adapter; structuring uses a live MiniMax M3 adapter (OpenAI-compatible endpoint, key server-side via environment) with a deterministic fixture fallback. `OQ-03` is resolved: private-network deployment, no authentication.

## Exact Commands

| Purpose | Command |
|---|---|
| Backend deps | `cd backend && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` |
| Format/lint backend | `cd backend && .venv/bin/ruff check --fix app tests && .venv/bin/ruff format app tests` |
| Typecheck backend | `cd backend && .venv/bin/mypy app` |
| Unit tests | `cd backend && .venv/bin/pytest tests/unit` |
| Integration/contract/security tests | `cd backend && .venv/bin/pytest tests/integration tests/contract tests/security` |
| Migrations (local) | `cd backend && .venv/bin/alembic upgrade head` |
| Backend dev server | `cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000` |
| Frontend deps | `cd frontend && npm install` |
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend lint/typecheck/build | `cd frontend && npm run lint && npm run typecheck && npm run build` |
| E2E | `cd e2e && npx playwright test` |
| Compose start | `docker compose up --build` |

---

## 1. Preconditions and Authority

Read completely before implementation:

1. `AGENTS.md`
2. `docs/PRODUCT_REQUIREMENTS.md`
3. `docs/DOMAIN_AND_AI_CONTRACTS.md`
4. `docs/UX_SPEC.md`

Do not begin feature code until Task 0 records exact stack choices, commands, and generated framework paths. After Task 0, update this document once with the concrete equivalents of all `<...>` placeholders; do not create a second implementation plan.

## 2. Target Logical Layout

Keep these logical modules even if the selected framework requires additional route/build files:

```text
backend/
  app/
    domain/               # entities, value objects, pure rules, invariants (no infra imports)
    application/          # use cases and transaction orchestration
    infrastructure/
      db/                 # schema, migrations, repositories
      recipe/             # retrieval and structuring adapters, safe fetch
      logging/            # redaction and operation IDs
    api/                  # FastAPI routers wrapping application operations
  tests/
    unit/
    integration/
    contract/
    security/
  alembic/
frontend/
  src/
    components/           # Food Tokens, tiles, rails, recipe components
    features/             # storage, rescue, recipes, history
    i18n/                 # English and Simplified Chinese resources
    api/                  # typed client for the application service
data/
  food-library.json       # importable bilingual seed fixture
e2e/                      # Playwright browser tests
compose.yaml
Dockerfile
.env.example
```

Domain code must not import UI, HTTP, database, or provider packages. In the per-task file lists below, `src/domain/*` and `src/application/*` map to `backend/app/...`, `src/infrastructure/*` maps to `backend/app/infrastructure/...`, `src/ui/*` maps to `frontend/src/...`, `tests/unit|integration|contract` map to `backend/tests/...`, and `tests/e2e` maps to `e2e/`.

## 3. Delivery Strategy

- Protect P0; cut P1/P2 before weakening correctness or visual polish.
- Use vertical slices that end in a testable user outcome.
- For domain and mutation behavior, write failing tests first.
- Use deterministic provider fixtures until a live provider is selected.
- Keep the application demoable after every completed slice.
- Commit small coherent changes once the workspace is a Git repository.

## Task 0 — Close Decisions and Scaffold the Repository

**Requirements:** `OQ-01`, `OQ-02`, `OQ-03`; `FR-DEP-*`

**Files:**

- Modify: `docs/PRODUCT_REQUIREMENTS.md` Open Decisions
- Modify: `docs/IMPLEMENTATION_PLAN.md` Tech Stack and commands
- Create: framework/package manifests selected by the user
- Create: `.env.example`
- Create: `compose.yaml`
- Create: `Dockerfile`

**Steps:**

1. Ask the user to choose or delegate application stack, live recipe providers, and deployment exposure.
2. Record the decisions and official documentation links; do not install external integrations before approval.
3. Initialize the repository and one application service using the selected package manager.
4. Materialize the logical directories above.
5. Add exact commands to this plan for format, lint, typecheck, unit, integration, E2E, build, Compose start, and migration.
6. Add one health endpoint and a boot smoke test.
7. Add `.env.example` with names only, no secrets.
8. Verify fresh local start and Compose start.

**Exit criteria:** Exact stack/commands are documented; application and test harness boot; no feature behavior exists yet.

## Task 1 — Domain Primitives and Invariant Tests

**Requirements:** `FR-INV-*`, `FR-STO-*`, `FR-EDT-003..005`, `FR-COOK-004..007`; all domain invariants

**Files:**

- Create: `src/domain/food-definition.*`
- Create: `src/domain/inventory-lot.*`
- Create: `src/domain/urgency.*`
- Create: `src/domain/quantity.*`
- Create: `src/domain/recipe.*`
- Create: `src/domain/allocation.*`
- Test: `tests/unit/domain/*`

**Steps:**

1. Write failing tests for calendar-day shelf-life arithmetic and five urgency boundaries.
2. Implement date rules using configured user locale/time zone without timestamp conversion errors.
3. Write failing tests for decimal quantities, compatible unit conversion, rounding increments, and prohibited cross-dimension conversion.
4. Implement quantity value objects and FoodDefinition conversion metadata.
5. Write failing tests for portion scaling, qualitative amounts, and back-normalizing an edited effective amount.
6. Implement recipe amount rules.
7. Write failing tests for selected-lot-first and first-expire-first-out allocation, no-date-last behavior, shortfalls, and no-negative invariants.
8. Implement pure allocation preview logic.
9. Add property/invariant tests for non-negative quantities and allocation bounds.
10. Run format, typecheck, and unit tests.

**Exit criteria:** All core rules are deterministic pure code with passing unit/property tests and no infrastructure imports.

## Task 2 — Relational Schema, Repositories, and Seed Library

**Requirements:** `FR-LIB-*`, `FR-INV-004`, `FR-HIS-*`, `NFR-REL-002`

**Files:**

- Create: `src/infrastructure/db/schema/*`
- Create: `src/infrastructure/db/migrations/*`
- Create: `src/infrastructure/db/repositories/*`
- Create: `data/food-library.json`
- Test: `tests/integration/db/*`

**Steps:**

1. Write repository contract tests for every entity in Domain Contracts.
2. Create migrations for FoodDefinition, ShelfLifeRule, InventoryLot, RescueSession, recipe entities, CookingSession, InventoryTransaction, and ActivityEvent.
3. Add constraints for enums, uniqueness, non-negative quantity, immutable transaction identity, and idempotency keys.
4. Seed the seven-food demo fixture plus common Fridge/Freezer/Pantry staples with English and Chinese names.
5. Implement repositories and transaction boundary helper.
6. Test fresh migration, seed idempotency, restart persistence, and ActivityEvent snapshots.
7. Test compensating transaction storage without deleting the original record.

**Exit criteria:** A fresh database migrates/seeds, repositories satisfy contracts, and restart preserves records.

## Task 3 — Add Food and Storage Operations

**Requirements:** `FR-LIB-*`, `FR-INV-*`, `FR-STO-*`, `UJ-01`, `UJ-05`

**Files:**

- Create: `src/application/food-library/*`
- Create: `src/application/inventory/*`
- Create: server endpoints/actions for library search, check-in, overview, detail, edit, move, reduce, discard, and undo
- Test: `tests/integration/inventory/*`

**Steps:**

1. Write failing integration tests for locale-aware library typeahead and custom-food creation.
2. Implement search over canonical names and aliases.
3. Write failing tests for check-in defaults, override source, invalid date/quantity, and idempotent duplicate submit.
4. Implement atomic check-in plus History event.
5. Write failing tests for Storage aggregation, Use Soon duplication by view, and most-urgent-lot surface state.
6. Implement overview queries.
7. Write failing tests for edit, move, manual reduction, discard, stale preview, and Undo.
8. Implement operations with atomic transactions and compensating reversal.

**Exit criteria:** All inventory use cases work through application operations with integration coverage; providers are not required.

## Task 4 — Storage, Add Food, and Manual Correction UI

**Requirements:** `UI-01`, `UI-02`, `UI-03`, `FR-RWD-001`, `FR-I18N-*`

**Files:**

- Create: `src/ui/components/food-token/*`
- Create: `src/ui/components/storage-tile/*`
- Create: `src/ui/features/storage/*`
- Create: `src/ui/i18n/en.*`
- Create: `src/ui/i18n/zh-CN.*`
- Test: `tests/e2e/storage.*`

**Steps:**

1. Build semantic visual tokens and one coherent Food Token registry with monogram fallback.
2. Implement Storage hierarchy: complete Use Soon, scopes, and dense complete grid.
3. Implement Add Food with typeahead, suggestion tiles, segmented location, quantity/presets, stored date, expiration shortcuts, and Save.
4. Implement ingredient detail and manual Reduce stock.
5. Add loading, empty, disconnected, validation, stale, success, and Undo states.
6. Add English and Chinese resources without inline user-facing strings.
7. Add component accessibility tests and mobile/desktop E2E for `UJ-01` and `UJ-05`.
8. Compare mobile Storage against `docs/visuals/storage-and-rescue.png` without tracing generated assets.

**Exit criteria:** Storage and inventory maintenance are usable, localized, accessible, responsive, and independent of recipe providers.

## Task 5 — Persisted Rescue Selection and Recent Searches

**Requirements:** `FR-RES-*`, `UI-04`, `UI-05`, `AC-RES-*`

**Files:**

- Create: `src/application/rescue/*`
- Create: `src/ui/features/rescue/*`
- Test: `tests/unit/rescue/*`
- Test: `tests/e2e/rescue-selection.*`

**Steps:**

1. Write failing tests for maximum seven, ordered selection, draft autosave, search freeze, and edit-as-new-draft semantics.
2. Implement RescueSession operations and persistence.
3. Build the seven-slot rail and full-screen complete Storage picker.
4. Implement capacity-disabled states, deselection, Done, and selection restoration.
5. Add Recent searches and last-view restoration using deterministic fixtures.
6. Verify accessible slot labels, 44 px targets, focus return, Chinese layout, and reduced motion.

**Exit criteria:** A selection survives restart, cannot exceed seven, and reopens in stable order without recipe providers.

## Task 6 — Recipe Provider Interfaces and Security Boundary

**Requirements:** `FR-SRC-*`, `FR-AI-*`, `NFR-SEC-*`, `ERR-01..05`

**Files:**

- Create: `src/infrastructure/recipe/retrieval-adapter.*`
- Create: `src/infrastructure/recipe/structuring-adapter.*`
- Create: `src/infrastructure/recipe/fixture-adapter.*`
- Create: `src/infrastructure/recipe/safe-fetch.*`
- Test: `tests/contract/recipe-adapters/*`
- Test: `tests/security/source-fetch/*`

**Steps:**

1. Define versioned internal retrieval and normalized-recipe schemas from Domain Contracts.
2. Write adapter contract tests before a live provider implementation.
3. Implement deterministic fixture adapters for the three V7 source patterns and AI plan.
4. Write SSRF tests for schemes, loopback/private/link-local/metadata targets, redirects, DNS changes, size, type, and timeout.
5. Implement the safe-fetch boundary and sanitized normalized output.
6. Implement at most one structured-output repair attempt and explicit error classification.
7. If `OQ-02` is approved, implement live adapters behind the same contracts and keep fixture mode.
8. Scan client bundles/logs for provider secrets and raw page bodies.

**Exit criteria:** Adapter tests pass with fixtures; security boundary fails closed; live provider is optional and replaceable.

## Task 7 — Recipe Results and AI Cooking Plan

**Requirements:** `FR-SRC-*`, `FR-AI-*`, `UI-06`, `AC-SRC-*`, `AC-AI-01`

**Files:**

- Create: `src/application/recipe-search/*`
- Create: `src/ui/components/recipe-match-belt/*`
- Create: `src/ui/features/recipe-results/*`
- Test: `tests/unit/recipe-search/*`
- Test: `tests/e2e/recipe-results.*`

**Steps:**

1. Write tests for source allow-list enforcement and stable selected-food usage arrays.
2. Implement search orchestration and persisted Rescue result snapshot.
3. Build the `Using` strip, source cards, fixed bright/dark belt, dual actions, and safe external link.
4. Implement AI Cooking Plan generation/display after sources with ingredients and amounts visible.
5. Implement separate source-analysis and plan-generation loading/error states.
6. Preserve sources when AI plan fails and preserve valid partial sources when others fail.
7. Verify no coverage score, Uses/Not used grouping, speculative missing-ingredient sentence, avatar, or required photo exists.

**Exit criteria:** Fixture-mode Results matches the written contract on mobile and desktop and persists across restart.

## Task 8 — Canonical Recipe Editor and Saved Recipes

**Requirements:** `FR-EDT-*`, `FR-RCP-*`, `UI-07..09`, `UJ-03`, `UJ-06`

**Files:**

- Create: `src/application/recipes/*`
- Create: `src/ui/features/recipe-editor/*`
- Create: `src/ui/features/saved-recipes/*`
- Test: `tests/unit/recipe-scaling/*`
- Test: `tests/integration/recipes/*`
- Test: `tests/e2e/recipe-editor.*`

**Steps:**

1. Write tests that AI plan, source analysis, and SavedRecipe all map into one RecipeDraft editor model.
2. Implement draft autosave and clear Draft saved versus Saved states.
3. Build inline Name/Description, provenance, plain-language full-recipe servings, portion controls, ingredient grid, freely addable/removable instructions, explicit Saved Recipes action, and reconciliation action.
4. Implement numeric/qualitative amount editing and base-value back-normalization.
5. Implement unlimited Add from Storage with `In recipe`, duplicate prevention, and As needed default.
6. Implement explicit SavedRecipe create/update and Recipes cards.
7. Implement Cook again through the same editor and current-availability derivation.
8. Add partial analysis/Needs review, save failure, stale availability, and unsaved-discard states.

**Exit criteria:** All recipe origins share one editor; scaling invariants pass; Saved Recipes remain curated and image-independent.

## Task 9 — Cooking, Reconciliation, History, and Undo

**Requirements:** `FR-COOK-*`, `FR-HIS-*`, `UI-10`, `UI-11`, `UJ-04`

**Files:**

- Create: `src/application/cooking/*`
- Create: `src/application/history/*`
- Create: `src/ui/features/cooking/*`
- Create: `src/ui/features/history/*`
- Test: `tests/integration/cooking/*`
- Test: `tests/e2e/cooking-history.*`

**Steps:**

1. Write failing tests for cook-time auto-save and immutable recipe snapshot.
2. Implement non-mutating CookingSession start.
3. Build What did you use with prefilled amounts, include/exclude, edit, Add food, oldest-items explanation, and one Update storage action.
4. Write injected-failure and stale-preview integration tests proving all-or-nothing commit.
5. Implement atomic/idempotent cooking commit.
6. Build History events and compensating Undo.
7. Test duplicate submit, provider outage during cooking, restart after review/commit, and reversal math.
8. Verify no Twin Diff, aggregate total, or second review screen is introduced.

**Exit criteria:** Cooking updates Storage once, never partially, remains auditable, and reverses through compensating records.

## Task 10 — Accessibility, Responsive Parity, Performance, and Polish

**Requirements:** `FR-RWD-*`, `FR-I18N-*`, all `NFR-A11Y-*`, `NFR-PERF-*`, UX state matrix

**Files:**

- Modify: all P0 UI features
- Create/modify: `tests/e2e/accessibility.*`
- Create/modify: `tests/e2e/responsive.*`
- Create: performance fixture/profile scripts selected in Task 0

**Steps:**

1. Run automated accessibility scans on every P0 route and fix violations.
2. Manually verify keyboard order, focus traps/restoration, live regions, reduced motion, 200% zoom, and touch targets.
3. Run complete English and Chinese golden paths at mobile and desktop viewports.
4. Ensure desktop uses equal-width deterministic wrapping and exposes every mobile capability.
5. Measure Storage usable time and P95 CRUD with the specified household fixture.
6. Optimize only measured bottlenecks; preserve semantic HTML and visual hierarchy.
7. Add visual regression baselines from implemented components, not generated-image pixel matching.

**Exit criteria:** Accessibility, parity, localization, and performance targets pass with recorded evidence.

## Task 11 — Docker, Operations, and Release Gate

**Requirements:** `FR-DEP-*`, `NFR-SEC-*`, `NFR-REL-*`, `NFR-OBS-*`, `AC-DEP-01`

**Files:**

- Modify: `Dockerfile`
- Modify: `compose.yaml`
- Modify: `.env.example`
- Create: `docs/DEPLOYMENT.md` as the canonical operations runbook
- Modify: `README.md` with deployment summary and runbook link
- Test: deployment smoke scripts selected in Task 0

**Steps:**

1. Build a non-secret image and run Compose from a clean persistent volume.
2. Verify health, migrations, seed behavior, restart persistence, and provider-disabled mode.
3. Document named volume, manual backup, restore, and upgrade caveats.
4. Document private-network default and reverse-proxy authentication requirement for external exposure.
5. Run secret scan and confirm credentials/raw pages are absent from client bundles and logs.
6. Run the full P0 verification suite and the complete mobile/desktop demo loop.
7. Record known P1/P2 omissions without weakening P0 claims.

**Exit criteria:** All release gates pass; a fresh private server can deploy, restart, and preserve data from documented commands.

## 4. Suggested One-to-Three-Day Schedule

| Window | Target slices |
|---|---|
| Day 1 | Tasks 0–4: foundation, domain, database, Add Food, Storage, manual correction. |
| Day 2 | Tasks 5–8: Rescue persistence, fixture providers, Results, AI plan, Recipe Editor, Saved Recipes. |
| Day 3 | Tasks 9–11: reconciliation, History/Undo, responsive/a11y polish, Docker, demo verification. |

If only one or two days are available, keep deterministic fixture adapters and cut live web retrieval before cutting inventory correctness, editable reconciliation, or polished mobile Storage.

## 5. Hackathon Cut Line

Cut in this order when time is constrained:

1. P1 Food Library management UI; keep seed/import plus minimal custom food.
2. Advanced search filters and recipe step editing.
3. Remembered portion preference.
4. Live provider breadth; retain one approved provider or deterministic demo fixture.
5. Desktop-specific enhancement; retain functional parity through straightforward responsive layout.

Never cut:

- explicit source provenance;
- Storage/Add Food availability during provider failure;
- non-negative, atomic, idempotent mutations;
- user review before Storage change;
- SavedRecipe/History distinction;
- mobile usability;
- no-auth private-deployment warning.

## 6. Final Release Gates

1. All P0 acceptance criteria in Product Requirements pass.
2. Complete golden loop passes at one mobile and one desktop viewport in English; core navigation also passes in Simplified Chinese.
3. No known path creates negative inventory, partial commits, duplicate commits, or invisible mutation.
4. Recipe results expose valid provenance or fail closed.
5. Storage, Add Food, manual correction, Saved Recipes, and History remain usable without a recipe provider.
6. Fresh Compose start, restart persistence, health, backup, and restore are verified.
7. No secret or raw retrieved content appears in client output or logs.
8. Canonical documentation still matches implemented behavior.
