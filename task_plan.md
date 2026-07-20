# Fridge Pal delivery work

## Completed: Tasks 6–11 (Golden Loop fully implemented)

### Final state
- 219 backend tests passing, 43 source files mypy-clean, 137 frontend modules building clean.
- All P0 features implemented: Storage, Add Food, Rescue selection, Recipe Results (AI + sources), Recipe Editor, Saved Recipes, Cooking reconciliation, History + Undo.
- Docker Compose config validated; secret scan clean; full release gate passes.

### Remaining open items
- Live-mode smoke test with real DeepSeek/Tavily keys (fixture-mode suite is green; live path covered by mocked-HTTP tests only).
- Task 10 polish can continue further (more e2e coverage, visual regression baselines, performance profiling).

### Phases (all complete)
1. [complete] Task 6 — Recipe provider adapter layer (schemas, retrieval/structuring protocols, Tavily + OpenAI-compatible adapters, fixtures, SSRF safe-fetch, factory, errors). 52 tests.
2. [complete] Task 7 — Rescue search pipeline + Results UI (RescueSessionRow, RescueService, API, frontend API-driven RecipeResultsView with loading/error/empty). 6 tests.
3. [complete] Task 8 — Server-backed Saved Recipes + Recipe Editor wiring (SavedRecipeRow, RecipeService CRUD, API, recipeStore localStorage→API, RecipeEditorView fetches rescue session). 7 tests.
4. [complete] Task 9 — History timeline + compensating Undo (HistoryService, undo_activity with compensating transactions, API, HistoryView replacing ComingSoonView). 7 tests.
5. [complete] Task 10 — Accessibility/responsive polish (skip-to-content link, touch target fixes, color contrast fix, desktop media queries).
6. [complete] Task 11 — Docker/Operations/Release Gate (compose config valid, full test suite green, secret scan clean).

---

## Previous task: AI provider integration (recipe retrieval + structuring)

### Goal
Give Fridge Pal real AI capabilities behind the existing provider-neutral adapter contracts: live recipe-source retrieval via Tavily search and live recipe structuring (AI Cooking Plan / source analysis) via an OpenAI-compatible LLM endpoint (default DeepSeek), always with deterministic fixture fallback.

### Scope decisions
- Provider configuration is vendor-neutral: `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` and `SEARCH_API_KEY` / `SEARCH_BASE_URL`; provider swap touches only `backend/app/infrastructure/recipe/factory.py`.
- Structuring default endpoint/model: `https://api.deepseek.com/v1`, `deepseek-chat` (user-supplied key; MiniMax Coding Plan key rejected on ToS/model-scope grounds).
- Retrieval: Tavily live search (user-supplied key); the search query is composed from selected ingredient names, quantities, and serving count only — never expiry/urgency.
- MiniMax M3 has no server-side web search, and an LLM must never invent source URLs; retrieval therefore needs a real search API or the fixture.
- Fixture mode remains the default and must keep the whole app demo-able offline with no keys.
- AI/provider output can propose structured data only; it never writes inventory. `Update storage` stays the mutation gate.
- Live provider errors are classified (ERR-01..05), at most one automatic structured-output repair attempt, then visible failure with fixture-independent Storage still usable.
- User has placed real keys in `backend/.env` (not committed).

### Phases
1. [complete] Decide providers (DeepSeek structuring, Tavily retrieval) and vendor-neutral env naming with the user.
2. [complete] Implement Task 6 adapter layer: versioned schemas, retrieval/structuring protocols, Tavily + OpenAI-compatible live adapters, deterministic fixtures, SSRF safe-fetch boundary, factory, config rename.
3. [complete] Contract + security tests (52 new; 193 total passing), Ruff and mypy clean; update `OQ-02` in PRD and Implementation Plan, `.env.example`, `compose.yaml`, `DEPLOYMENT.md`.
4. [pending] Smoke-test live mode with the user's real keys (fixture-mode suite already green; live path so far only covered by mocked-HTTP tests).
5. [pending] Task 7 — Recipe Results and AI Cooking Plan: search orchestration, persisted Rescue result snapshot, API endpoints, source cards with fixed seven-slot belt and dual actions, AI plan display with ingredient quantities, separate loading/error states.
6. [pending] Continue ordered slices: Task 8 (canonical Recipe Editor + Saved Recipes), Task 9 (cooking/reconciliation/history/undo) per `docs/IMPLEMENTATION_PLAN.md`.

---

## Previous task: Docker Compose deployment documentation

### Goal
Make a fresh private Linux server deployment repeatable through Docker Compose and document the real project structure for humans and agents.

### Scope decisions
- Docker Compose is the only production deployment target for this slice.
- Direct server-IP access is supported through an explicit `0.0.0.0` bind and a trusted-source firewall rule.
- No domain, TLS proxy, Vercel adaptation, or application authentication is added.
- Deployment documentation is canonical at `docs/DEPLOYMENT.md`; README remains the concise entry point.

### Phases
1. [complete] Confirm Docker Compose over Vercel and approve the deployment boundary.
2. [complete] Re-read canonical requirements and inspect the current container/runtime configuration.
3. [complete] Harden Compose, the image build, and the environment template.
4. [complete] Write the deployment runbook and restructure README.
5. [complete] Validate configuration, image build, full Compose lifecycle, backup/restore, and the regression suite.

---

## Previous task: interaction clarity passes

## Goal
Make recipe and food editing direct, understandable, visually consistent, and truthful about when Storage changes.

Current extension: reduce redundant source-card signals and make Storage quantity, date, and location semantics immediately distinguishable.

## Scope decisions
- Recipe instructions can be added and removed freely.
- Replace internal or ambiguous copy such as “Original yield”, “Save draft”, and “Cook this” with outcome-oriented language.
- Food editing directly accepts quantity and a general unit; no steppers or change-effect hints.
- Stored date and use-by date are editable and persisted through the existing idempotent mutation path.
- Fridge and Freezer badges must be visually distinct.
- Add meaningful icons to actions and field groups; no decorative icons.
- Keep tests minimal: mutation contract test plus lint, typecheck, build, and focused browser inspection.
- Seven-food context uses one neutral tray language from Rescue through Meal Ideas; source usage is conveyed by token brightness/recession, never a dark-blue container.
- Source and AI plan editor entry points share one concise icon-plus-label action: `Edit recipe`.
- Source navigation is one concise icon-plus-label action: `Website`; source cards never show estimated time.
- Explain once that source details are AI-organized and may be incomplete.
- Recipe source belts use only full-color/elevated versus dimmed/recessed states; no duplicate check or minus marks.
- Freezer uses icy blue, Fridge uses fresh green, and every location selector reuses the same icon/color language.
- Storage quantities always include a unit and use a distinct value treatment; urgency uses a time-state treatment, with a tombstone icon for `Past date` but no food-safety claim.
- Inventory counts stay outside the location-filter row so large values cannot collide with tabs.

## Phases
1. [complete] Inspect the canonical contracts and current mutation/editor implementations.
2. [complete] Write and run a failing backend mutation contract test for editable unit and stored date.
3. [complete] Extend backend/frontend inventory mutation contracts and documentation.
4. [complete] Refactor Food Edit into a direct, attractive form.
5. [complete] Refactor Recipe Editor instructions, language, actions, units, and semantic icons.
6. [complete] Adjust location colors and visually verify representative screens.
7. [complete] Run focused verification and report results.
8. [complete] Update source-result contracts, copy, and fixture shape.
9. [complete] Unify seven-food match-belt styling with the Rescue selection tray.
10. [complete] Simplify source cards and align editor actions.
11. [complete] Verify Meal Ideas visually and run frontend checks.
12. [complete] Simplify source-result state and actions with concise semantic icons.
13. [complete] Extract one reusable location icon/filter system and swap Fridge/Freezer color meaning.
14. [complete] Separate Storage quantity, urgency, and inventory-count hierarchy.
15. [complete] Update canonical UI contracts and localization.
16. [complete] Run focused static/build checks and browser inspection.
17. [complete] Add failing contracts for canonical unit validation, conversion, and legacy normalization.
18. [complete] Implement canonical backend unit handling and safe same-dimension conversion.
19. [complete] Replace every Storage unit text field with a canonical dropdown.
20. [complete] Remove the ambiguous quantity icon and update canonical documentation.
21. [complete] Run focused backend/frontend verification and browser inspection.

## Errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| PATCH lot ignored `unit`/`storedOn`; focused test expected `g` but received `piece`. | 1 | Expected RED state; extend request and transactional edit service next. |
| Repository search included a non-existent top-level `data/` path and stopped before later reads. | 1 | Remove that path and run targeted reads separately. |
| Whitespace-only unit passed the initial `min_length` check before normalization. | 1 | Added a failing contract assertion and reject an empty normalized unit in the request validator. |
| System Homebrew Node 18 could not load the removed ICU 70 dynamic library after restart. | 1 | Use the Codex bundled workspace Node runtime for frontend checks; no dependency reinstall required. |
| `command -v -a` is not valid zsh syntax, and the assumed `/Applications/Codex.app` path does not exist on this install. | 1 | `which -a` located the working NVM Node 22 runtime; invoke its Node/npm CLI explicitly. |
| NVM npm started correctly, but package scripts resolved project `.bin` shims pinned to Homebrew Node 18. | 2 | Bypass the stale shims and invoke ESLint, vue-tsc, and Vite entrypoints directly with NVM Node 22. |
| Initial browser connection used an unsupported import, then treated an `openTabs()` descriptor as a controlled tab and passed its id to `tabs.get()`. | 1 | Reused the installed browser runtime and claimed the exact user-tab descriptor with `browser.user.claimTab(...)`. |
| Called screenshot through the Playwright helper, where that method does not exist. | 1 | Used the documented tab-level `screenshot(...)` method. |
| Attempted to remove an i18n duplicate that was only duplicated in an earlier truncated output, not in the file. | 1 | Verified with `rg`; each locale has exactly one `lastCooked`/`emptyTitle` entry, so no edit was needed. |
| The combined build/residue-scan command ran from `frontend/` while the scan used root-relative paths. | 1 | The production build itself passed; reran the residue scan and `git diff --check` from the repository root. |
| The first focused pytest command assumed a root-level `.venv`. | 1 | The project virtual environment is `backend/.venv`; reran the exact RED tests through that interpreter. |
| The legacy-normalization test assumed inventory query ordering. | 1 | Compared the food-key/quantity mapping instead; Storage ordering is not part of that migration contract. |
| Food Edit rendered before its unit draft was initialized and attempted `g → piece`. | 1 | Added an explicit draft-ready gate so conversion and dirty-state calculations begin only after lot data synchronizes. |
| Compose validation without `.env` stopped on the required MySQL password. | 1 | Validated with `--env-file .env.example`; production still requires a private `.env`. |
| Docker Buildx could not write its activity cache inside the workspace sandbox. | 1 | Re-ran the build through the approved Docker Compose permission boundary. |
| The configured DaoCloud Docker Hub mirror returned `401` while resolving the optional Dockerfile syntax image. | 1 | Removed the unused syntax directive; the retry built the complete image successfully. |
| Fresh MySQL startup failed while demo seeding because a child ActivityEvent flushed before its new FoodDefinition parent. | 1 | Added a foreign-key-enabled regression test and explicitly flushed each new parent before adding child rows. |
| Production Vue history route `/rescue` returned 404 on direct refresh. | 1 | Added an SPA static-serving contract and an index fallback for extensionless client routes while preserving missing-asset 404s. |
| `mysqldump` requested `PROCESS` privilege for tablespace metadata when run as the least-privileged app user. | 1 | Added `--no-tablespaces`; no database privilege escalation is required. |
