# Warm-Refinement UI Redesign — Design

**Status:** Approved by user (2026-07-18)
**Scope:** Visual restyle + motion system. No functional, routing, store, or i18n copy changes. No structural refactors (e.g. no shared AppHeader extraction).
**Canonical constraints:** `docs/UX_SPEC.md` remains authoritative. All product invariants in `AGENTS.md` remain in force.

## 1. Direction

"Warm refinement": keep the cream/coral/navy identity from UX_SPEC §6 and the visual boards, but raise perceived quality through finer color grading, layered elevation, better typographic hierarchy, and a complete (currently missing) motion system.

## 2. Token Layer (`frontend/src/styles/tokens.css`)

The two-tier token system (raw `--frd-*` → semantic `--color-*`) stays. Changes concentrate in values, not names; new tokens are added where needed.

### Color

- Canvas: keep warm cream; add an extremely subtle warm radial page ambience via `--color-canvas-glow` (optional, disabled under `prefers-reduced-motion` nothing to do with motion — purely decorative gradient, kept subtle per "dense but calm").
- Urgency scale: keep full-tile urgency surfaces (UI-CMP-02 invariant). Refine the five levels into softer, more graded tints; every level keeps its WCAG-AA-verified ink pairing (≥4.5:1). Each tile gets a same-hue accent edge (1px inner border) for definition without hard outlines.
- Navy/ink: slightly deepen the rail navy and add a subtle vertical gradient on dark rails (SelectionRail, RecipeMatchBelt, sticky Using strip); selected slots gain a restrained light halo.
- Primary blue: keep `#0B5DEB` family; add hover/active shades.
- Replace the two hardcoded blues in the AI plan card (`#b8cef7`, `#cbd9f3`) with tokens.

### Elevation

- Move from single flat shadows to 2–3 layer soft shadows tinted with the existing navy shadow hue: resting card, raised (hover/sticky), and overlay (sheets/dialogs).
- Dark rails keep recessed inset shadow; selected tokens get light elevation + halo.

### Radius

- Cards/tiles: 14–16px. Controls (chips, inputs, buttons): 10–12px. Keep `--radius-full` only for true pills (chips' existing pill use stays as-is where already present; no new pill-everything).

### Typography

- Keep the system font stack (bilingual + offline deployment constraint; no webfonts).
- Rebuild the type scale: larger display size for screen headlines with negative letter-spacing (~-0.02em); clearer body/caption hierarchy; `font-variant-numeric: tabular-nums` on quantities and step numbers.

## 3. Component Refinements

- **AppNav**: replace Unicode placeholder glyphs (▣ ◉ ◇ ◷) with a coherent set of hand-drawn 24px stroke SVG icons (fridge/box, rescue, chef hat/book, clock). Active tab gets a sliding indicator + color transition; keep backdrop blur and 44px targets; desktop rail mirrors the same icons.
- **StorageTile**: urgency tiles gain a soft inner highlight (top), same-hue accent edge, and a gentle resting shadow; quantity becomes visually secondary per UI-CMP-02 but crisper via tabular-nums.
- **AppButton / AppChip**: refined hover lift, pressed scale (0.97), and consistent focus rings via tokens.
- **AI Cooking Plan card**: token-driven brand gradient (primary → surface), no hardcoded hex; keep layout and content contract unchanged.
- Replace repeated translucent header/nav background literals (`rgb(246 244 238 / 0.94)`, `rgb(255 255 255 / 0.96)`) with `--color-header-bg` / `--color-nav-bg` tokens (value-only cleanup, not a structural refactor).

## 4. Motion System (`base.css` + component styles)

Currently only 3 transitions exist app-wide. Add:

1. **Route transitions**: forward navigation = subtle slide-from-right + fade; back = slide-from-left; tab switches = fade only. Implemented via `<router-view v-slot>` + `<Transition>` in `App.vue`, keyed by route, with direction from a tiny navigation-direction composable.
2. **First-paint stagger**: grids (Storage, Use Soon, picker, ingredients) fade/rise in with ≤40ms stagger; a 7-item stagger completes <350ms per UX_SPEC §8.
3. **Selection feedback**: picker/rail/chip selection uses `--ease-pop` scale pop (defined but unused today); match-belt slots animate bright/dark state in place (no reordering, per UI-CMP-04).
4. **Overlays**: bottom sheets / dialogs slide-and-fade in; fixed action bars rise on mount.
5. **Tab indicator**: sliding underline/pill in AppNav.

Global limits (UX_SPEC §8): individual motion ≤240ms, easing via existing `--ease-*` tokens; full `prefers-reduced-motion` disable (extend the existing kill-switch to cover all new transitions). No meaning ever depends on motion.

## 5. Explicitly Out of Scope

- Any functional/logic/store/API/router change; any i18n copy change.
- Structural refactors (shared AppHeader component, CSS consolidation beyond the header-bg token).
- Dark theme (tokens stay structured for it).
- Anything in UX_SPEC §11 prohibited patterns.

## 6. Verification

- `npm run typecheck` / lint clean in `frontend/`.
- Existing e2e suite (`e2e/`, Playwright) still passes; add/adjust selectors only if a class rename breaks a test (avoid renaming contract classes).
- Manual check at 390×844 and one desktop viewport: urgency AA contrast, reduced-motion on, zh-CN locale, tab/rail animations under budget.
