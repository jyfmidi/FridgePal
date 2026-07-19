# Fridgital Product Requirements

**Status:** Canonical specification for implementation  
**Product stage:** Hackathon MVP  
**Implementation status:** Not started  
**Primary user:** A solo home cook living alone  
**Deployment:** Private, single-user, Docker Compose

## 1. Product Definition

Fridgital is a digital twin of food stored in a household fridge, freezer, and pantry. It reduces food waste by making inventory easy to capture, expiration risk easy to scan, and recipe rescue easy to complete without losing inventory accuracy.

**Primary promise:** Turn food that is about to expire into tonight's meal.

**Golden loop:** Capture → Notice → Select → Research → Edit → Cook → Reconcile.

## 2. Goals and Success Criteria

| ID | Goal | MVP success evidence |
|---|---|---|
| `PG-01` | Keep a trustworthy digital twin. | The user can add, inspect, edit, reduce, discard, and undo inventory without negative quantities or hidden mutations. |
| `PG-02` | Surface expiration risk at a glance. | All near-expiry foods appear together and retain visible urgency in complete Storage. |
| `PG-03` | Turn selected food into grounded cooking options. | Results retain source provenance and show exactly which selected foods each source uses. |
| `PG-04` | Make recipes personal and reusable. | AI or source-derived recipes can be edited, scaled, saved, reopened, and cooked again. |
| `PG-05` | Close the loop after cooking. | Actual usage is editable before one atomic Storage update and History record. |
| `PG-06` | Produce a persuasive hackathon demo in one to three development days. | The complete golden loop works on mobile and desktop and deploys through Docker Compose. |

## 3. Canonical Glossary

| Term | Definition | User-facing? |
|---|---|---|
| `FoodDefinition` | Canonical food identity, aliases, unit, visual key, defaults, and shelf-life rules. | Food name only. |
| `InventoryLot` | One acquired batch of a food with quantity, location, stored date, and optional expiration date. | Exposed only in detail/review. |
| Storage | Complete inventory truth across Fridge, Freezer, and Pantry. | Yes. |
| Use Soon | Derived view of active lots inside the configured expiration-attention window. | Yes. |
| `RescueSession` | Internal persisted object for an ordered food selection, search results, AI plan, and restoration state. | No. Use `Recent searches`, `Using`, and `Change foods`. |
| Recipe Source | A grounded external recipe result with publisher and URL. | Yes. |
| AI Cooking Plan | A normalized recipe synthesized from retrieved sources and selected foods. | Yes. |
| `RecipeDraft` | Autosaved editable recipe originating from an AI plan, analyzed source, or saved recipe. | Presented as Recipe Editor. |
| Saved Recipe | Curated reusable recipe stored in Recipes. | Yes. |
| `CookingSession` | Snapshot of a recipe portion plus proposed and confirmed inventory usage. | Presented through Cook and reconciliation. |
| History | Append-only user-readable activity and reversal timeline. | Yes. |

Never expose the obsolete terms `Combination`, `Query Capsule`, `Twin Diff`, or FEFO in ordinary UI copy.

## 4. Scope and Priority

### 4.1 P0 — Required for the Hackathon MVP

- Seeded food library, typeahead check-in, and minimal custom-food creation.
- Fridge, Freezer, and Pantry inventory with lot-level persistence.
- Complete Storage, Use Soon, five-level urgency, and direct inventory correction.
- Persistent maximum-seven Rescue selection and recent-search restoration.
- Source-grounded recipe discovery with provenance and fixed ingredient-use mapping.
- AI Cooking Plan and source-to-recipe analysis.
- Canonical Recipe Editor, portion scaling, Storage-linked ingredient addition, and Saved Recipes.
- Editable cooking reconciliation, manual stock reduction, atomic mutation, History, and Undo.
- English and Simplified Chinese architecture.
- Mobile/desktop feature parity, accessibility baseline, and Docker Compose deployment.

### 4.2 P1 — Implement Only After the Golden Loop Is Stable

- Full Food Library management UI for aliases, presets, visuals, and shelf-life rules.
- Advanced lot-detail allocation controls.
- Search filters such as time, cuisine, or dietary intent.
- Recipe step editing beyond a compact secondary edit action.
- Remembered personal portion preference.

### 4.3 P2 — Deferred

- Accounts, shared households, and permissions.
- Photo recognition, barcode scanning, and receipt import.
- Notifications and background reminders.
- Shopping lists, nutrition tracking, and long-term meal planning.
- Custom storage spaces and shelf maps.
- Public SaaS deployment.

## 5. Functional Requirements

### 5.1 Food Library and Check-In

| ID | Pri | Requirement |
|---|---:|---|
| `FR-LIB-001` | P0 | Seed common foods with localized names, aliases, category, Food Token key, natural base unit, package presets, recommended storage, and storage-specific shelf-life defaults. |
| `FR-LIB-002` | P0 | Add Food begins with typeahead search and recent/common suggestions; photo recognition is not the primary path. |
| `FR-LIB-003` | P0 | If no match exists, create a minimal custom food with localized name, base unit, storage default, and optional shelf-life rule. |
| `FR-LIB-004` | P0 | A food without curated art receives a deterministic colored monogram based on its first user-perceived localized grapheme. |
| `FR-INV-001` | P0 | Selecting a food pre-fills its recommended storage, natural unit, package/quantity presets, `stored_on = today`, and a suggested expiration date. |
| `FR-INV-002` | P0 | Suggested expiration equals `stored_on + ShelfLifeRule.duration_days`; the user can override it with one-tap relative options or a date picker. |
| `FR-INV-003` | P0 | The UI never labels `stored_on` as a production date and identifies whether expiration came from a library default or user override. |
| `FR-INV-004` | P0 | Saving creates one InventoryLot and one History event only after explicit confirmation. |
| `FR-INV-005` | P0 | Storage unit entry is a dropdown limited to `g`, `kg`, `ml`, `l`, and `piece`. Each FoodDefinition retains one base unit; compatible `g↔kg` and `ml↔l` check-ins convert exactly into that base unit before persistence. Food-specific count aliases are rejected. |

### 5.2 Storage and Inventory Truth

| ID | Pri | Requirement |
|---|---:|---|
| `FR-STO-001` | P0 | Support exactly three MVP locations: Fridge, Freezer, and Pantry. |
| `FR-STO-002` | P0 | Storage opens with a complete Use Soon section followed by the complete scoped inventory. |
| `FR-STO-003` | P0 | An urgent food appears in both Use Soon and its normal complete-inventory position; both views reference the same lots. |
| `FR-STO-004` | P0 | Overview tiles aggregate active lots of the same food and location into one quantity; do not display lot-count badges such as `×2`. |
| `FR-STO-005` | P0 | Tiles show Food Token/monogram, localized name, aggregate quantity, unit, and explicit urgency copy where applicable. |
| `FR-STO-006` | P0 | Urgency uses five derived levels: Past date, Today, 1–2 days, 3–5 days, and Later. Do not make food-safety claims. |
| `FR-STO-007` | P0 | Ingredient detail supports direct quantity and canonical-unit dropdown correction, stored-date edit, location move, expiration edit, consumed reduction, discard, and access to underlying lots. Same-dimension base-unit changes convert every lot transactionally; cross-dimension conversion is never guessed. |
| `FR-STO-008` | P0 | Manual `Reduce stock` works without a recipe, accepts an amount, previews the affected food, and records a reversible transaction. |
| `FR-STO-009` | P0 | No operation may persist a negative lot quantity. |

### 5.3 Rescue and Search Persistence

| ID | Pri | Requirement |
|---|---:|---|
| `FR-RES-001` | P0 | Rescue begins with one ordered seven-slot selection bar; selected slots show Food Tokens and empty slots show `+`. |
| `FR-RES-002` | P0 | `+` or `Edit foods` opens a full-screen Storage multi-select picker with All, Fridge, Freezer, and Pantry scopes. |
| `FR-RES-003` | P0 | Rescue contains at most seven foods. At capacity, other foods remain visible but cannot be selected until one is removed. |
| `FR-RES-004` | P0 | Selection order remains stable in the Results `Using` strip and every recipe match belt. |
| `FR-RES-005` | P0 | Draft selection persists across closing/reopening the application. |
| `FR-RES-006` | P0 | Starting search freezes an immutable result snapshot. `Change foods` creates an edited draft and new search rather than silently rewriting old results. |
| `FR-RES-007` | P0 | Recent searches retain selected-food snapshots, results, AI plan state, timestamp, and last view; the user can reopen the previous result set in one action. |

### 5.4 Recipe Sources and AI Cooking Plan

| ID | Pri | Requirement |
|---|---:|---|
| `FR-SRC-001` | P0 | Search uses selected canonical foods and urgency as explicit constraints and returns grounded source URLs, titles, publishers, and retrieval timestamps. |
| `FR-SRC-002` | P0 | Each source card shows title, publisher/domain, a clear AI-organized/incomplete-data notice, and a fixed seven-slot ingredient-use belt. Estimated duration is never shown on source cards; other metadata is optional and omission-safe. |
| `FR-SRC-003` | P0 | Used slots are bright/elevated and unused slots are dimmed/recessed without duplicate check/minus marks, reordering, Uses/Not used groups, fractions, percentages, or coverage scores. Accessible labels retain the used/not-used meaning. |
| `FR-SRC-004` | P0 | Every source exposes separate icon-plus-label `Website` and `Edit recipe` actions. The AI Cooking Plan uses the same `Edit recipe` label for the shared editor destination. |
| `FR-SRC-005` | P0 | Source cards do not claim speculative natural-language missing ingredients such as `You'll also need …`. |
| `FR-AI-001` | P0 | AI Cooking Plan appears after source results and visibly includes title, description, base yield, ingredient names/amounts/units, instructions preview, contributing-source count, and `Edit recipe`. |
| `FR-AI-002` | P0 | `Edit recipe` analyzes the selected source into the same normalized RecipeDraft schema used by the AI Cooking Plan. |
| `FR-AI-003` | P0 | All displayed AI/source-derived fields retain provenance or an explicit `Needs review` state; invalid structured output is never presented as verified source truth. |
| `FR-AI-004` | P0 | Provider failure may disable discovery but never blocks Storage, Add Food, manual inventory actions, Saved Recipes, or History. |

### 5.5 Recipe Editor and Saved Recipes

| ID | Pri | Requirement |
|---|---:|---|
| `FR-EDT-001` | P0 | AI plans, analyzed sources, and saved recipes open one canonical Recipe Editor. |
| `FR-EDT-002` | P0 | Recipe Editor exposes editable Name, Description, base yield, portion, ingredients, and ordered instructions that can be freely added or removed; Name is required to save. |
| `FR-EDT-003` | P0 | Numeric ingredient amounts derive from normalized base amounts and a positive decimal multiplier; qualitative amounts such as `To taste` do not scale. |
| `FR-EDT-004` | P0 | Show recipe context and how many servings the full recipe makes before portion adjustment. Provide `0.5×`, `Full recipe`, and `Custom`; retrieved/AI recipes may begin at the solo-cook `0.5×` preference without overwriting base values. |
| `FR-EDT-005` | P0 | Editing an effective amount at a non-original multiplier updates the normalized base amount so future scaling remains coherent. |
| `FR-EDT-006` | P0 | `+ Add from storage` opens a complete Storage multi-select picker with no seven-food limit, prevents duplicates, and marks `In recipe` foods. |
| `FR-EDT-007` | P0 | Newly added Storage foods default to `As needed` until the user chooses a numeric or qualitative amount. Adding/editing never changes Storage. |
| `FR-EDT-008` | P0 | Recipe drafts autosave internally but do not appear in Recipes until explicit Save or cooking begins. |
| `FR-RCP-001` | P0 | `Save to Recipes` creates a SavedRecipe and `Update saved recipe` updates one; `Review use & update Storage` automatically saves an unsaved draft before opening reconciliation. |
| `FR-RCP-002` | P0 | Recipes cards use ingredient-token identity, name, description, origin, optional last-used portion, and `Cook again`; photography is optional, never required. |
| `FR-RCP-003` | P0 | Opening or cooking again routes through Recipe Editor so portion and ingredients can be reviewed. Current Storage availability is derived on open and never persisted as recipe truth. |

### 5.6 Cooking, Reconciliation, History, and Undo

| ID | Pri | Requirement |
|---|---:|---|
| `FR-COOK-001` | P0 | `Review use & update Storage` opens one `What did you use?` surface with scaled recipe amounts prefilled. Starting or cancelling reconciliation does not mutate Storage. |
| `FR-COOK-002` | P0 | The user can include/exclude ingredients, edit actual amounts, and add another Storage food used while improvising. |
| `FR-COOK-003` | P0 | `Update storage` is the only cooking mutation gate and clearly states that nothing changes before confirmation. |
| `FR-COOK-004` | P0 | Allocation consumes explicitly selected lots first, then active lots of the same food in first-expire-first-out order, with no-date lots last. |
| `FR-COOK-005` | P0 | If demand exceeds availability, cap the proposal at available quantity, expose the shortfall, and require user review. |
| `FR-COOK-006` | P0 | One atomic, idempotent commit writes all InventoryTransactions, CookingSession completion, and History events or writes none. |
| `FR-COOK-007` | P0 | If inventory changed after preview, reject the stale commit, recalculate affected lines, and require reconfirmation. |
| `FR-HIS-001` | P0 | History is append-only and contains check-in, edit, move, manual reduction, discard, rescue search, saved recipe, cooking, deduction, and reversal events. |
| `FR-HIS-002` | P0 | Undo creates compensating transactions/events linked to the original event; it never deletes audit history. |

### 5.7 Responsive, Localization, and Deployment

| ID | Pri | Requirement |
|---|---:|---|
| `FR-RWD-001` | P0 | Mobile and desktop expose the same functional set. Layout, packing, and navigation placement may adapt; workflows and permissions may not. |
| `FR-I18N-001` | P0 | Initial locales are English and Simplified Chinese; English is the initial primary locale. |
| `FR-I18N-002` | P0 | Localize food names, UI copy, dates, relative time, numbers, units, and list formatting. Do not hard-code English widths. |
| `FR-DEP-001` | P0 | Deploy as a single-user private application through Docker Compose with persistent data in a named/documented volume. |
| `FR-DEP-002` | P0 | The MVP has no authentication and must warn that unprotected public exposure is unsupported. |

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| `NFR-SEC-001` | Provider and database credentials remain server-side and never enter client bundles, URLs, analytics, or logs. |
| `NFR-SEC-002` | Source fetching blocks loopback, private, link-local, and metadata-service destinations; limits schemes, redirects, content type, response size, and duration. |
| `NFR-SEC-003` | Render sanitized normalized text only; never render retrieved HTML or persist full raw pages. |
| `NFR-A11Y-001` | P0 flows target WCAG 2.2 AA, keyboard operation, visible focus, focus restoration, and no keyboard traps. |
| `NFR-A11Y-002` | Touch targets are at least 44 × 44 CSS pixels where possible; status never depends on color, hover, position, or motion alone. |
| `NFR-A11Y-003` | Respect reduced motion and support 200% zoom without losing primary actions or requiring two-dimensional scrolling. |
| `NFR-PERF-001` | Local interaction feedback appears within 100 ms. |
| `NFR-PERF-002` | Excluding external providers, P95 CRUD requests finish within 500 ms for 500 active lots and 10,000 History events on the documented minimum server profile. |
| `NFR-PERF-003` | Storage reaches usable content within 2.5 seconds on a representative mid-tier mobile device after assets are cached. |
| `NFR-REL-001` | Recipe search shows loading within 200 ms and has a configurable default hard timeout of 20 seconds. |
| `NFR-REL-002` | Service restart preserves food library, inventory, Rescue sessions, recipes, cooking, transactions, and History. |
| `NFR-OBS-001` | Structured logs use operation IDs, redact secrets, and exclude raw retrieved page bodies. |

## 7. Primary User Journeys

### `UJ-01` — Fast Check-In

1. Open Add Food from Storage.
2. Search or choose a common FoodDefinition.
3. Review compact defaults for quantity, unit, location, stored date, and expiration.
4. Change exceptions and save.
5. See the Food Token appear in Storage and History.

### `UJ-02` — Rescue Expiring Food

1. Inspect Use Soon.
2. Open Rescue and choose up to seven Storage foods.
3. Find meal ideas.
4. Compare source cards using the stable bright/dark belt.
5. Reopen the result later through Recent searches if needed.

### `UJ-03` — Turn a Result Into a Recipe

1. Choose `Edit recipe` on either the AI Cooking Plan or a source.
2. Review provenance and any `Needs review` fields.
3. Edit Name/Description, portion, ingredients, and instructions.
4. Add Storage ingredients if desired.
5. Save or Cook.

### `UJ-04` — Cook and Reconcile

1. Review the recipe and portion.
2. Tap `Review use & update Storage`; unsaved work becomes a SavedRecipe.
3. Adjust actual usage in `What did you use?`.
4. Confirm `Update storage`.
5. See updated Storage and an Undo-capable History event.

### `UJ-05` — Keep the Twin Honest Without a Recipe

1. Open a Storage food or the manual reduction action.
2. Enter actual amount consumed or discarded.
3. Confirm once.
4. See aggregate quantity update and a reversible History event.

### `UJ-06` — Cook a Saved Recipe Again

1. Open Recipes and select a SavedRecipe.
2. Re-enter Recipe Editor, adjust portion, and review current availability.
3. Cook and reconcile through the same flow as `UJ-04`.

## 8. Acceptance Criteria

| ID | Given | When | Then |
|---|---|---|---|
| `AC-INV-01` | A FoodDefinition has a Fridge shelf-life rule | The user selects it in Add Food | Storage defaults to Fridge, `stored_on` defaults to today, and expiration is derived but editable. |
| `AC-INV-02` | Two active lots contain the same food in one location | Storage renders the overview | One tile shows the summed quantity and no lot-count multiplier. |
| `AC-INV-03` | A FoodDefinition base unit is `g` | The user checks in `0.5 kg` | One new lot stores `500 g`; repeated requests remain idempotent and no `kg` lot is mixed into the aggregate. |
| `AC-INV-04` | An existing local FoodDefinition uses `head`, `bulb`, `clove`, or `bunch` | The canonical-unit migration runs | The unit becomes `piece`, the numeric lot quantities stay unchanged, and subsequent runs make no further mutation. |
| `AC-STO-01` | Seven foods are inside the attention window | Storage opens | All seven appear in Use Soon and also remain in complete inventory. |
| `AC-RES-01` | Five Rescue slots are filled | The user taps an empty slot | The complete Storage picker opens, permits two more selections, and blocks an eighth. |
| `AC-RES-02` | A searched RescueSession exists | The application is closed and reopened | Recent searches restores its exact selected order and result snapshot. |
| `AC-SRC-01` | A result uses four of seven selected foods | The source card renders | All seven slots remain ordered; four are bright and three dark, with accessible used/not-used labels and no score. |
| `AC-SRC-02` | A source result exists | The user chooses `Website` versus `Edit recipe` | The first opens the safe external URL; the second creates/analyzes a RecipeDraft. |
| `AC-AI-01` | Grounded sources were retrieved | AI Cooking Plan renders | Ingredient amounts and provenance are visible before Recipe Editor is opened. |
| `AC-EDT-01` | A two-serving base recipe is open | The user selects `0.5×` | Effective numeric amounts and serving count halve while base amounts remain unchanged. |
| `AC-EDT-02` | Six foods are already in a recipe | The user opens Add from Storage | Existing foods show `In recipe`, duplicates are blocked, and any number of other foods may be added. |
| `AC-RCP-01` | An unsaved RecipeDraft is open | The user taps `Review use & update Storage` | A SavedRecipe is created before reconciliation, and cooking continues without a second save prompt. |
| `AC-COOK-01` | A valid deduction preview exists | The user confirms Update Storage | All lot deltas and History entries commit atomically and quantities stay non-negative. |
| `AC-COOK-02` | Inventory changed after preview | The user submits the stale preview | Nothing commits; affected values recalculate and require reconfirmation. |
| `AC-HIS-01` | A cooking commit completed | The user activates Undo | Compensating transactions restore the prior totals and both original and reversal remain in History. |
| `AC-I18N-01` | Locale is Simplified Chinese | The user opens every P0 screen | Copy, food names, date/number/unit formats, and layout render without losing actions. |
| `AC-DEP-01` | A fresh server has Docker Compose and valid configuration | The documented start command runs | The app becomes healthy, and data survives a service restart. |

## 9. Traceability Matrix

| Product goal | Functional requirements | Journeys | Primary verification |
|---|---|---|---|
| `PG-01` | `FR-INV-*`, `FR-STO-*`, `FR-COOK-*`, `FR-HIS-*` | `UJ-01`, `UJ-04`, `UJ-05` | Unit invariants, transaction integration tests, `AC-INV-*`, `AC-COOK-*`, `AC-HIS-01` |
| `PG-02` | `FR-STO-002..006` | `UJ-02` | Urgency boundary tests, visual regression, `AC-STO-01` |
| `PG-03` | `FR-RES-*`, `FR-SRC-*`, `FR-AI-*` | `UJ-02`, `UJ-03` | Adapter contracts, result E2E, `AC-RES-*`, `AC-SRC-*`, `AC-AI-01` |
| `PG-04` | `FR-EDT-*`, `FR-RCP-*` | `UJ-03`, `UJ-06` | Scaling unit tests, editor E2E, `AC-EDT-*`, `AC-RCP-01` |
| `PG-05` | `FR-COOK-*`, `FR-HIS-*` | `UJ-04`, `UJ-05` | Atomicity/idempotency integration tests, `AC-COOK-*`, `AC-HIS-01` |
| `PG-06` | All P0 plus `FR-DEP-*` | Complete golden loop | Mobile/desktop E2E and Docker smoke, `AC-DEP-01` |

## 10. Open Decisions

| ID | Decision required | Resolution |
|---|---|---|
| `OQ-01` | Application framework, persistence library, and test stack. | **Resolved (user-selected):** Vite + Vue 3 + TypeScript client; FastAPI (Python) application service; SQLAlchemy 2 + Alembic on MySQL 8 in deployment, SQLite for local tests; pytest + Playwright. |
| `OQ-02` | Recipe retrieval and recipe-structuring provider(s). | **Resolved:** Provider-neutral adapter contracts first. Retrieval ships with a deterministic curated fixture adapter (MiniMax M3 has no server-side web search). Structuring uses a live MiniMax M3 adapter (`https://api.minimax.io/v1/chat/completions`, model `MiniMax-M3`, key server-side only) with a deterministic fixture fallback. |
| `OQ-03` | Deployment exposure. | **Resolved:** Private LAN/loopback binding, no authentication; reverse-proxy authentication is required before any public exposure. |
| `OQ-04` | Seed-library breadth and initial bilingual translations. | Seed only the demo foods plus common household staples, with an importable data file. |

No coding agent may infer external providers, install integrations, or broaden scope merely because an open decision exists.
