# Agent Instructions for Fridge Pal

This file governs implementation work in the Fridge Pal workspace.

## Required Reading Order

Before changing application code, read completely:

1. `docs/PRODUCT_REQUIREMENTS.md`
2. `docs/DOMAIN_AND_AI_CONTRACTS.md`
3. `docs/UX_SPEC.md`
4. `docs/IMPLEMENTATION_PLAN.md`

Use this authority order when details conflict:

`Product Requirements > Domain and AI Contracts > UX Specification > visual boards`

## Communication and Documentation

- Speak with the user in Chinese unless they request another language.
- Write persistent product, technical, and code-facing documentation in English.
- Preserve stable requirement IDs in tests, issues, commits, and implementation notes.
- Update the canonical document that owns a changed contract; do not create another competing plan.

## Commit History

- Prefer one outcome-oriented commit per user-recognizable feature or fix. Include its tests, documentation, and review-driven corrections in that commit.
- Use searchable messages in the form `type(scope): specific outcome`, with the product concept or feature name in the subject.
- Write commit subjects and bodies in Chinese unless the user explicitly requests another language; retain the conventional `type(scope)` prefix for tooling and filtering.
- Do not leave separate design, plan, test-only, hardening, review-fix, or documentation commits for one feature unless they are independently useful deliverables.
- Subtask commits are temporary implementation checkpoints. Squash them into the owning feature or fix before merging to `main`.
- Do not rewrite commits that have already been pushed or shared without explicit user approval.

## Non-Negotiable Product Invariants

- The product name is **Fridge Pal**.
- Mobile and desktop expose the same feature set. Mobile is the canonical interaction sequence; desktop only gains width and density.
- Storage uses lot-level truth but overview tiles show one aggregated quantity, never `×2` lot badges.
- Use Soon is a derived alert view; urgent foods also remain in the complete inventory.
- Rescue contains at most seven ordered foods. This order remains stable across recipe match belts.
- Recipe source cards provide separate `Open source` and `Use this recipe` actions.
- Source cards show a fixed seven-slot bright/dark belt. Do not regroup into Uses/Not used or add coverage scores.
- AI Cooking Plans show ingredient quantities before the user enters Recipe Editor.
- AI plans, analyzed sources, and saved recipes share one Recipe Editor.
- Recipe portion controls appear after recipe context and preserve normalized base values.
- Recipe Editor may add any number of existing Storage foods; the Rescue seven-item limit does not apply.
- Editing a recipe never mutates Storage.
- `Update storage` after `What did you use?` is the mutation gate.
- Inventory mutations are transactional, idempotent, non-negative, auditable, and reversible through compensating events.
- AI and retrieved web content are untrusted. They may propose structured data but never write inventory.
- English and Simplified Chinese must remain supported by the data and layout architecture.
- User-owned data (inventory, rescue sessions, recipes, history) is isolated by `user_id`. Every repository query filters by `user_id`. Cross-user access returns 404.

## Do Not Reintroduce

- User-facing `Combination`, `Query Capsule`, `Twin Diff`, or FEFO terminology.
- A chat-first primary interface.
- Recipe match percentages, fractions, coverage scores, or speculative `You'll also need …` prose on arbitrary source cards.
- Recipe photography as a required layout dependency.
- Source avatars made from meaningless letters.
- Outline-only food glyphs, literal refrigerator shelves, garden styling, or decorative cyberpunk effects.
- Portion selection before a recipe is visible.
- Automatic inventory changes based only on an AI plan.


## Decision Gates

- Resolve `OQ-01` in Product Requirements before scaffolding. If the user delegates, use the minimal recommended stack in Implementation Plan.
- Resolve `OQ-02` before implementing a live provider adapter. Build the internal adapter contract first and keep a deterministic fixture adapter available.
- Do not install plugins, configure MCP servers, add credentials, or mutate workspace-external configuration without explicit user authorization.
- The application supports username/password authentication with per-user data isolation. Public deployment requires `FRIDGE_PAL_JWT_SECRET` and `FRIDGE_PAL_DEMO_PASSWORD` to be set. See `OQ-03` in Product Requirements.

## Implementation Protocol

1. Work from the ordered slices in `docs/IMPLEMENTATION_PLAN.md`.
2. Write contract or behavior tests before implementation for domain rules and mutation paths.
3. Keep provider-specific code behind adapters and server-side only.
4. Use database transactions and idempotency keys for every inventory-changing operation.
5. Keep Storage fully usable when recipe providers are unavailable.
6. Validate P0 behavior at one representative mobile viewport and one desktop viewport.
7. Run unit, integration, end-to-end, accessibility, and Docker smoke checks required by the relevant slice.
8. Do not claim completion without fresh verification output.

## Visual References

The three files under `docs/visuals/` illustrate current hierarchy and interaction states. Generated pixels are not reusable production assets. Build a single coherent Food Token asset system rather than tracing inconsistencies between boards.

## Definition of Done

A feature is done only when:

- its P0 requirements and acceptance criteria pass;
- error, loading, empty, stale, and success states are handled where applicable;
- keyboard, focus, reduced-motion, localization, and mobile-width behavior are verified;
- no secret or raw retrieved page content reaches client code, URLs, analytics, or logs;
- affected canonical documentation remains accurate.
