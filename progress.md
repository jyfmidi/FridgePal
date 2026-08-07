# Progress

## 2026-08-01 (preset food icon system)

- Started discovery for the new admin-managed preset-food icon workflow.
- Loaded the required brainstorming, image-generation, and file-based planning instructions.
- Confirmed the initial worktree is clean and the latest commit owns the new admin Food Library console.
- Created the current task phases and recorded the first constraints; no application code or image assets have been changed yet.
- Read the four canonical documents completely in the required authority order.
- Captured the Food Token production constraints and the admin custom-icon size/security contract in `findings.md`.
- Audited the latest admin commit and traced Food Token use across its major rendering surfaces.
- Inspected the existing Vue/SVG registry, demo catalog, dev token showcase, and all three visual boards; recorded the current 16-food baseline and style anatomy.
- The first local Vite preview attempt hit the repository's already-known broken Homebrew Node 18/ICU link; logged it and switched to the working workspace Node path instead of changing dependencies.
- Started Vite successfully with the bundled Node runtime after approving the local-only bind. The first browser view confirmed that `/dev/tokens` is gated by normal app boot and therefore also needs an isolated local API before its content renders.
- Started an isolated temporary SQLite-backed API, inspected the actual `/dev/tokens` size ramp and the Chinese admin “新增食材” icon picker, then cleanly stopped both local servers. No normal application data was touched.
- Completed project discovery. The next design decision is the production asset format; generation and application-code changes remain paused until that direction is approved.
- User selected production option 1: code-native Vue/SVG curated icons. Recorded the decision; the remaining scope question is whether to refine the existing 16 while expanding the library.
- User selected full unification: 16 current icons plus 24 new staples, 40 total. Scope clarification is complete; visual-route comparison is next.
- User approved visual route 1 (`Bold Pantry`). Approach comparison is complete; incremental design approval now moves to the exact 40-key catalog.
- Began an official-source audit against the Chinese Dietary Guidelines (2022). Initial finding: the proposed catalog needs stronger whole-grain, mixed-bean, soybean, and nut representation before it should be approved.
- Completed the first official-source pass. The guide supplies five food groups plus examples—not a fixed import list—and supports replacing three lower-priority draft icons with sweet potato, mixed beans, and nuts.
- Reopened the first-batch count at the user's request. The 40-icon catalog is now a review baseline, not an approved final scope; next is a complete inventory and vegetable-gap review.
- User rejected the dietary-group-driven additions and clarified the product taxonomy: mixed beans are too generic; olive oil is a condiment; nuts are snacks; rice, pasta, and bread are staples; fruit coverage is insufficient.
- Audited public Hema and Xiaoxiang material for item-level popularity evidence. Confirmed that no public stable nationwide SKU leaderboard is available; recorded local/seasonal sales examples and Hema category-growth signals without treating them as national ranks.
- Added the Ministry of Agriculture and Rural Affairs' nationally monitored 28-vegetable and 6-fruit baskets as the core demand proxy. The next design review will use this evidence to present a fresh-cooking master catalog and a priority first batch.
- User corrected the emphasis: stop market research and simply assemble a useful set of common concrete ingredients. Refocused the catalog on an uncomplicated household list with stronger Chinese vegetable and fruit coverage.
- User approved the 70-food scope and requested generation.
- Read the image-generation, brainstorming, planning, implementation-plan, TDD, review, and verification instructions. Based on the established Vue/SVG system, selected direct code-native SVG generation rather than a raster generation/tracing detour.
- Wrote and committed the approved design as `4955f3d docs: define common food icon library`.
- Inspected the current 16-key registry, development showcase, admin picker, e2e harness, and demo seed. Confirmed the icon expansion can remain frontend-only and must not silently seed inventory or mutate user FoodDefinition rows.
- Created the detailed TDD implementation plan at `docs/plans/2026-08-01-common-food-icon-library.md`; implementation will proceed locally in this task because no subagent workflow was requested.
- Added the RED browser contracts. The showcase contract failed with 16 cells versus the required 72; the admin contract timed out exactly while waiting for the absent `Use icon apple` option. Both failures demonstrate the missing catalog rather than a test setup error.
- Added the typed SVG primitive, palette, and Vue component-factory foundation. Focused ESLint and corrected vue-tsc checks pass; the catalog remains intentionally RED until category definitions are registered.
- Implemented 38 vegetable/fungi/aromatic, 18 fruit, 10 protein/aquatic, 4 soy/chilled, and 2 compatibility SVG definitions and registered all 72 keys through Vue components.
- GREEN confirmed: the desktop showcase contract renders 72 curated SVG cells, and the focused admin flow can select `apple`, save a preset, find it in Add Food, and clean it up. Focused icon lint and full frontend typecheck pass.
- Expanded the development size ramp to cover leafy, pale, fruit, meat, aquatic, and chilled silhouettes. Added the reusable production/reference prompt guide and linked it from the canonical UX contract.
- Fresh frontend verification passes after documentation/showcase integration: ESLint, vue-tsc, and Vite production build (164 modules).
- Generated deterministic Playwright visual baselines for the complete 72-key registry on both white and neutral tray backgrounds and inspected both at original resolution.
- Added and inspected a 24/32/48/64 px visual baseline. Applied targeted silhouette fixes for bitter melon, bean sprouts, and mango, then re-inspected the complete 72-key board.
- Saved the reviewed complete-board preview at `docs/visuals/food-token-library.png` and removed the temporary platform-specific Playwright snapshots.
- Removed the 16 superseded one-off Vue icon components after confirming the registry has no remaining imports; the category catalog is now the single geometry source.
- Final verification passes: frontend ESLint, vue-tsc, Vite production build (164 modules), `git diff --check`, and all 38 Playwright mobile/desktop tests.

## 2026-07-21 (commit readiness)

- Audited branch `codex/animated-loader-icons`: six loader/icon commits plus 34 unstaged paths; no staged changes.
- Fresh verification: frontend ESLint, vue-tsc, Vite build, and `git diff --check` pass.
- Backend pytest produced the expected RED state for the date-coupled demo seed test: 207 passed, 1 failed (`Use Soon` 5 vs 7).
- Confirmed the root cause without modifying application behavior; next step is a test-only fixed-date seed injection.
- Added a test-only seed-date injection for `2026-07-18`; the focused integration test now passes (GREEN).
- Full verification passes: 208 backend tests, Ruff, Mypy (43 files), ESLint, vue-tsc, Vite production build (145 modules), `git diff --check`, and 18 Playwright mobile/desktop tests.
- Initial explicit `git add` was blocked because `.git` is read-only in the default sandbox; source files remain unchanged and unstaged.
- Created `e8089aa` for the deterministic demo-seed test fix.
- Created `460da8e` for the direct LLM Meal Ideas backend refactor and contracts.
- Created `5a8bff2` for the integrated Meal Ideas UI, looping loaders, History clarity, and browser regressions.
- Post-commit verification is green: 208 backend tests, Ruff, Mypy, ESLint, vue-tsc, Vite build, `git diff --check`, and 18 Playwright tests.

## 2026-07-20 (Tasks 6–11)
- Implemented Task 6 (recipe provider adapter layer), Task 7 (rescue search pipeline + results UI), Task 8 (server-backed saved recipes + recipe editor wiring), Task 9 (history timeline + compensating undo), and Task 10 (accessibility/responsive polish).
- Task 6: versioned schemas, retrieval/structuring protocols, Tavily + OpenAI-compatible live adapters, deterministic fixtures, SSRF safe-fetch, classified errors (ERR-01..05), factory. 52 contract/security tests.
- Task 7: `RescueSessionRow` persistence, `RescueService` (retrieval→structuring→snapshot), `POST /api/rescue/search`, `GET /api/rescue/{id}`. Frontend `RecipeResultsView` replaced fixtures with real API + loading/error/empty states. 6 contract tests.
- Task 8: `SavedRecipeRow`, `RecipeService` CRUD, `GET/POST/PATCH /api/recipes`. Frontend `recipeStore` migrated from localStorage to API. `RecipeEditorView` fetches rescue session data and uses API for save. `RecipesView` API-backed. 7 contract tests.
- Task 9: History service with `list_history()` and `undo_activity()` (compensating transactions restoring lot quantities/statuses). `GET /api/history`, `POST /api/history/{id}/undo` with idempotent replay. Frontend `HistoryView` replacing `ComingSoonView`, Undo button, chef/trash/undo icons. 7 contract tests.
- Task 10: Skip-to-content link, touch target fixes (AppChip 36px→44px, LocationFilterBar 40px→44px), color contrast fallback fix (#dc2626→#b91c1c), desktop @media queries for HistoryView and RescueView, `skipToContent` i18n keys.
- Task 11: Docker Compose config validation passes. Full release gate: 219 backend tests, Ruff, mypy, frontend ESLint, vue-tsc, Vite build (137 modules), compose config — all clean. Secret scan: no provider URLs or keys in client bundle; no hardcoded secrets in backend; `.env.example` has no real secrets.
- Final state: 219 backend tests passing, 43 source files mypy-clean, 137 frontend modules building clean. Golden Loop (Capture→Notice→Select→Research→Edit→Cook→Reconcile→History/Undo) fully implemented.
- Committed in 5 atomic commits: Task 6 (`919e856`), Task 7 (`d6ce4a9`), Task 8 (`a85f923`), Task 9 (`a16ccdf`), Task 10 (`0dc5c06`).

## 2026-07-20 (earlier)
- User decided the AI provider strategy: DeepSeek for recipe structuring (user has a pay-as-you-go key), Tavily for recipe-source retrieval (user has a key); MiniMax Coding Plan key rejected because Coding Plan keys are model-scoped and ToS-limited to coding tools.
- User required vendor-neutral configuration names so providers can be swapped later, and ruled that retrieval queries use ingredient names, quantities, and serving count only — not expiry/urgency.
- Implemented Task 6 adapter layer under `backend/app/infrastructure/recipe/`: versioned pydantic schemas, retrieval/structuring Protocols, `TavilyRetrievalAdapter`, `OpenAICompatibleStructuringAdapter` (one repair attempt, prompt-injection separation), deterministic fixture adapters, SSRF `safe_fetch` boundary, and a settings-driven `factory.py`.
- Replaced `MINIMAX_*` config with `LLM_*` and `SEARCH_*` in `config.py`, `.env.example`, `compose.yaml`, and `docs/DEPLOYMENT.md`.
- Added 52 contract/security tests (fixture determinism, schema rejection, allow-list citations, repair limit, error classification, SSRF cases; all HTTP mocked). Full suite: 193 passed; Ruff and mypy clean; no new dependencies (uses existing `httpx`).
- Updated `OQ-02` resolutions in `docs/PRODUCT_REQUIREMENTS.md` and `docs/IMPLEMENTATION_PLAN.md` to the DeepSeek + Tavily decision.
- User placed real DeepSeek and Tavily keys in `backend/.env`; live-mode smoke test and Task 7 (results UI + AI Cooking Plan orchestration) remain open.

## 2026-07-19
- User selected Docker Compose on a self-managed server instead of Vercel and approved direct IP access without a domain.
- Approved a two-container deployment design with configurable host binding, persistent MySQL, no bundled reverse proxy, and a dedicated agent-readable operations runbook.
- Re-read the four canonical documents and inspected the existing Compose, Dockerfile, environment, settings, database session, and package configuration.
- Added the approved deployment design and implementation plan under `docs/plans/`.
- Added `.dockerignore`, a non-root application runtime, configurable/safe Compose binding, restart and health policies, deterministic volume naming, and an expanded deployment environment template.
- Wrote `docs/DEPLOYMENT.md` with first install, IP access, firewall, health, upgrades, backup/restore, rollback, removal safety, troubleshooting, and agent execution instructions.
- `docker compose --env-file .env.example config --quiet` passes. The first image build reached an environment-specific `401` from the locally configured DaoCloud Docker Hub mirror while resolving the optional Dockerfile syntax image; removed that unnecessary directive before retrying.
- The retry built `fridgital-app` successfully: 430 KB build context, Vue production build with 134 modules, Python package installation, and non-root runtime image creation all completed.
- Fresh Compose smoke exposed and then verified two production-only bugs: strict MySQL foreign-key ordering during demo seed and Vue history-route refresh 404s. Added focused RED/GREEN integration contracts for both.
- The isolated stack now reaches healthy state, `/api/health` returns OK, `/rescue` returns 200, a missing asset remains 404, and the Storage response hash is identical across an app restart.
- The first backup command exposed MySQL 8.4's tablespace `PROCESS` privilege requirement; kept the database user least-privileged and changed the runbook to use `mysqldump --no-tablespaces`.
- Re-ran backup successfully and restored it into the isolated MySQL deployment; the post-restore Storage hash matched the pre-backup hash.
- Confirmed the application container runs as uid/gid `fridgital`, direct-IP config publishes `0.0.0.0:8080`, and MySQL remains unpublished.
- Full backend pytest, Ruff, mypy, frontend ESLint, vue-tsc, Vite build, and Compose config checks passed.
- Removed the exact temporary `fridgital-deploy-smoke` containers, network, and MySQL volume after validation; no user data or pre-existing Docker resource was touched.
- Confirmed Design B remains the approved direction: one semantic visual system across the app.
- Started the editor clarity pass.
- Chose a minimal verification strategy: mutation-path contract coverage plus static/build checks and focused browser inspection; no Playwright work.
- Re-read Product Requirements and Domain/AI Contracts before changing application code.
- Re-read UX Specification and Implementation Plan, then inspected the current backend mutation transaction and both editor views.
- RED confirmed: the focused PATCH-lot test failed because `unit` remained `piece`; `storedOn` was also not part of the current request model.
- GREEN confirmed: the new focused mutation contract passes after extending the request and transactional edit service.
- Audited the unit vocabulary and demo fixtures; identified all user-visible culinary-specific count units that need normalization.
- Implemented the backend/frontend edit contract, direct Food Edit form, step add/remove, simplified recipe actions, general-unit fixtures, semantic icons, and distinct Freezer color.
- `git diff --check` and all 7 focused inventory-mutation integration tests pass. The first frontend check attempt was blocked by a broken system Node/ICU link, not project code.
- Frontend ESLint and vue-tsc pass when invoked directly with the available NVM Node 22 runtime.
- Visually inspected Storage at the active mobile viewport; location badge separation and label readability are good.
- Visually inspected the Garlic editor and fixed route scroll restoration discovered during the check.
- Inspected the complete Recipe Editor at mobile width and interactively verified add/remove instructions.
- Final verification passed: backend Ruff, mypy, and all 7 inventory mutation integration tests; frontend ESLint, vue-tsc, and Vite production build (128 modules); `git diff --check`.
- Kept the live Recipe Editor tab open for user review.
- Started Meal Ideas source-trust and seven-food visual-continuity pass.
- Updated canonical requirements/UX/contracts, unified seven-food visuals, removed source timing metadata, added the AI-organized incompleteness notice, and aligned both editor entry actions.
- Final Meal Ideas verification passed: ESLint, vue-tsc, Vite production build (128 modules), `git diff --check`, old-copy/token residue scan, and mobile browser inspection.
- Kept the live Meal Ideas tab open for user review.
- Started the source-action and Storage information-hierarchy refinement pass.
- Confirmed the safe humor boundary: use a tombstone icon for `Past date` while retaining neutral date-status wording.
- Removed redundant source-belt state marks; shortened and iconized Website/Edit recipe/Change actions.
- Added reusable LocationIcon and LocationFilterBar components, applied them across Storage, Rescue picking, Add Food, Food Edit, and Recipe ingredient picking, and reassigned icy blue to Freezer.
- Separated Storage quantity, urgency, and inventory-count hierarchy; piece quantities now display an explicit unit.
- Updated Product Requirements, Domain/AI Contracts, and UX Specification to own the refined labels and visual semantics.
- ESLint, vue-tsc, production build (134 modules), and `git diff --check` pass; focused mobile browser checks passed for Recipe Sources and Storage location filtering.
- Restored the live Storage view to the complete `All` scope and kept it open for review.
- User approved the strict canonical-unit design: dropdown-only `g/kg/ml/l/piece`, exact same-dimension conversion, legacy count aliases normalized to `piece`, and no quantity icon.
- Added the approved design and implementation plan under `docs/plans/` and started the RED contract-test phase.
- RED confirmed all four missing contracts, then GREEN confirmed exact mass/volume check-in conversion, special-unit rejection, transactional all-lot unit conversion, legacy normalization, and the existing unit/date audit path.
- Replaced Add Food, aggregate Food Edit, and per-lot unit text fields with canonical dropdowns; compatible unit selection converts the displayed quantity instead of relabeling it.
- Removed the scale-like quantity icon from tiles and edit fields, retaining explicit Quantity copy and the distinct value capsule.
- Browser QA confirmed legacy-unit migration, singular/plural `piece(s)` copy, dropdown-only Add Food and Food Edit, and live `g↔kg` draft conversion. The QA interactions did not save or mutate inventory.
- Final verification passed: all 144 backend tests, Ruff, mypy, frontend ESLint, vue-tsc, Vite production build (134 modules), and `git diff --check`.
