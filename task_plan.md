# Fridgital interaction clarity passes

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
