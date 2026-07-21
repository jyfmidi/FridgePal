# Brand Polish and Layout Fixes Design

**Status:** Approved design, awaiting implementation
**Date:** 2026-07-21

## Goal

Make Fridge Pal feel branded, cheerful, and cohesive across every screen — starting from the currently bare login/register flow — and fix a set of known layout/consistency bugs (overflow risk, cramped spacing, inconsistent font sizes). The tone target is **playful and cute** ("活泼可爱") while staying inside the existing brand decision from `2026-07-19-fridge-pal-brand-design.md`: coral is the brand color, blue remains the interaction color, warm inventory/urgency surfaces stay unchanged.

Non-goals: no dark theme, no webfont (system font stack stays, per user decision), no information-architecture changes, no new features.

## 1. Design Language

### 1.1 Coral brand ramp enters the token system

The logo colors (`#F47B65` / `#EE6A56` / `#B84739`) currently exist only inside SVG files. Add them to `frontend/src/styles/tokens.css` as raw palette entries plus semantic aliases:

- `--color-brand` — primary coral, used for brand surfaces, highlights, badges
- `--color-brand-strong` — deeper coral (`#EE6A56`) for hover/active brand states
- `--color-brand-ink` — dark coral (`#B84739`) for text/icons on coral surfaces (verify ≥ 4.5:1 against the chosen surface; darken if needed)
- `--color-brand-soft` / `--color-brand-softer` — light coral tints for glows, empty-state washes, selected-brand backgrounds

Usage rule: **blue stays the action color** (primary buttons, selected filters, links). Coral is reserved for brand identity moments: logo contexts, the auth screens, empty states, the desktop sidebar brand block, and small accent details. This preserves the urgency ramp's semantic clarity (coral-adjacent hues already mean "expiring today") — brand coral must never tint inventory tiles or urgency badges.

### 1.2 The mascot as a recurring character

The fridge mark appears at:

- Login/register: large, centered, with a gentle bounce-in entrance
- Desktop sidebar top (currently an awkward ~88 px empty gap)
- Global page header (already present; verify the stale "Fridgital" wordmark is gone everywhere)
- Empty states (empty Storage, empty Recipes, empty History) with one line of friendly localized copy
- `FridgePalLoader` (already present)

Motion: entrance bounce uses the existing pop ease `cubic-bezier(0.34,1.4,0.64,1)`; a subtle hover wiggle on the header mark; everything disabled under `prefers-reduced-motion`.

### 1.3 Shape, depth, and press feedback

- Cards keep the current `--radius-card/xl`; auth card and empty-state cards may use `--radius-xl` for a softer feel. Do not pill-shape surfaces (UX_SPEC §6).
- Shadows stay the existing navy-tinted layered tokens.
- Add a uniform press state on tappable cards/buttons: `transform: scale(0.97)` with `--duration-fast`, plus the existing focus-visible ring.

### 1.4 Typography and voice

- System font stack stays; remove the unloaded `Inter` entry from `--font-family-sans` so the stack honestly reflects what renders (`SF Pro Text`/`system-ui` → PingFang SC / Microsoft YaHei fallbacks).
- Auth flow and logout get full i18n coverage (`auth.*` keys, en + zh-CN). Chinese copy tone: light and friendly (e.g. tagline "你的冰箱小管家"); English equivalent "Your fridge's best pal".

## 2. Login / Register Redesign

Current state: plain white card on canvas, text-only `<h1>Fridge Pal</h1>`, no logo, no i18n, raw `.auth-submit` button instead of `AppButton`, ~110 lines of CSS duplicated nearly verbatim between `LoginView.vue` and `RegisterView.vue`, no media queries (short landscape viewports can clip the centered card).

Design:

- **New `AuthLayout` component** shared by both views: cream canvas with a soft coral radial glow behind the top area; large brand mark (bounce-in); product name + localized tagline; white form card (`--radius-xl`, `--shadow-md`) below. On short viewports the layout scrolls instead of clipping.
- **New `AppInput` component**: label, input, error message, focus ring — one canonical field style. Login/register adopt it first; the component is designed to be reusable by AddFood / StorageItem / RecipeEditor later (adoption there is out of scope for this pass).
- Submit buttons switch to `AppButton` (primary, block).
- Both views consume `auth.*` i18n keys, including error fallbacks ('Login failed', 'Passwords do not match' are currently hardcoded English).
- `100vh` → `100dvh` for the auth page container.

## 3. Global Brand Touchpoints

- **Desktop sidebar (`AppNav.vue`)**: add a brand block (mark + "Fridge Pal" wordmark) at the top, replacing the current empty 88 px padding. Mobile bottom bar unchanged.
- **Page header (`AppPageHeader.vue`)**: keep mark + title; confirm no stale "Fridgital" strings remain user-facing.
- **Empty states**: Storage (no foods), Recipes (no saved recipes), History (no events) each get the mark, one friendly localized line, and the existing primary CTA. Keep it compact — "dense but calm", no oversized hero art.
- **`FridgePalLoader` dedup**: stop inlining the mark's SVG paths and hex fills; reference `public/brand/fridge-pal-mark.svg` (or a single shared mark component) so future logo changes cannot drift between two copies.
- **`index.html`**: add `theme-color` (brand coral) and `description` meta. `<html lang>` stays synchronized with the active locale (see §4).

## 4. Language Switcher (EN / 中文)

Current state: a toggle exists only inside `StorageView.vue:69` (`.locale-action`, shows 中文/EN) as a header action on one screen; `src/i18n/index.ts` hardcodes `locale: 'en'`; the auth flow is outside i18n entirely.

Design:

- Extract a small `useLocale` composable: holds the active locale, `setLocale()` updates vue-i18n, syncs `document.documentElement.lang`, and persists to `localStorage` (`fridge-pal-locale`).
- Initial locale: stored preference → browser `navigator.language` (zh* → `zh-CN`, else `en`) → `en`.
- Entry point: a 中文/EN control rendered by `AppPageHeader`'s action slot on every screen that uses it (replacing the Storage-only one-off), plus a text link on the auth screens (login/register) so logged-out users can switch too.
- Backend API calls that already accept `locale` (e.g. `src/api/rescue.ts`) continue to receive the active locale from the composable.

## 5. Layout / Consistency Bug Fixes

All verified by code inspection; each fix is small and independent.

| # | Issue | Location | Fix |
|---|---|---|---|
| B1 | `--color-text` is referenced but never defined (silently falls back to inherited color) | `App.vue:256`, `HistoryView.vue:369,468,501` | Replace with the appropriate `--color-ink*` token |
| B2 | z-index magic values `9998`/`9999` bypass the `--z-*` scale | `App.vue` | Map onto the z-index token scale |
| B3 | Nav labels render at 11 px (`0.6875rem`), below the smallest size token | `AppNav.vue` | Raise to `--font-size-xs` (12 px) |
| B4 | User widget is `position: fixed; top: 8px; right: 8px`, floating over the sticky page header and able to overlap its action slot | `App.vue:152` | Integrate into the header/sidebar layout flow instead of fixed overlay |
| B5 | Breakpoints 700 / 720 / 880 px used inconsistently across views and components | `MealIdeaDetailView`, `RecipeResultsView`, `AppPageHeader`, `AppNav`, `App.vue` | Standardize on two widths (720 and 880) with a header comment in `tokens.css` documenting the convention (CSS custom properties cannot be used in media queries) |
| B6 | Hardcoded fallback hexes `#b91c1c` / `#ef4444` outside the token palette | `RecipeResultsView.vue`, `RecipeEditorView.vue`, `HistoryView.vue` | Replace with `--color-danger` tokens |
| B7 | Auth pages can clip on short/landscape viewports (`min-height: 100vh` + centered grid) | `LoginView.vue`, `RegisterView.vue` | `100dvh` + scrollable layout (part of §2) |
| B8 | Hardcoded English "Logout" and auth strings outside i18n | `App.vue:97`, `LoginView.vue`, `RegisterView.vue` | Move to i18n keys (part of §2) |
| B9 | `Inter` listed first in the font stack but never loaded | `tokens.css:183` | Drop it from the stack (system fonts per user decision) |
| B10 | No `theme-color` / `description` meta; `lang` not synced with locale | `index.html` | Add meta; sync via `useLocale` (§4) |

## 6. Micro-interactions

- Uniform press feedback (`scale(0.97)`, `--duration-fast`) on tappable cards and buttons.
- Auth-page mark bounce-in; header mark hover wiggle.
- Existing `stagger-in` and route transitions stay; no new heavy animation.
- All new motion gated behind `prefers-reduced-motion`.

## 7. Implementation Phases

1. **P0 — Foundations**: coral ramp + semantic tokens; B1, B2, B5, B9 fixes; `AppInput` and `AuthLayout` extraction; `useLocale` composable.
2. **P1 — Auth screens**: new login/register layout, i18n coverage, B7, B8.
3. **P2 — Global touchpoints**: sidebar brand block, language switcher rollout (B4 in the same pass), empty states, loader dedup, index.html meta (B10).
4. **P3 — Consistency sweep**: B3, B6, remaining hardcoded sizes/colors; verify one mobile and one desktop viewport per AGENTS.md.

## 8. Verification

- Visual check at one mobile (390×844) and one desktop (1280×800) viewport for every touched screen, including a short landscape viewport for auth pages.
- Check brand coral is absent from inventory/urgency surfaces; check zh-CN rendering on every touched screen.
- `prefers-reduced-motion` emulation: no bounce/wiggle/press motion.
- Frontend lint, typecheck, build; existing e2e suite stays green; update snapshots/screens in `e2e/shots` if referenced.
- Keyboard focus order and focus-visible rings on the reworked auth screens and switcher.
- Grep for stale `Fridgital` and `--color-text` references after the pass.
