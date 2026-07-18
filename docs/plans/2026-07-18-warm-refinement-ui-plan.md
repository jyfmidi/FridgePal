# Warm-Refinement UI Redesign Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restyle the Fridgital frontend ("warm refinement") and add a complete motion system, without touching any functional logic.

**Architecture:** All changes are CSS values + scoped styles + minimal template/class additions. The two-tier token system in `frontend/src/styles/tokens.css` is remapped; new semantic tokens are added for header/nav translucency, rail gradients, and stagger motion. Motion lands via `base.css` utilities + `<Transition>` in `App.vue`.

**Tech Stack:** Vue 3 SFCs, plain CSS with custom properties, vue-router 4, Vite 6.

**Design reference:** `docs/plans/2026-07-18-warm-refinement-ui-design.md` (approved). Canonical constraints: `docs/UX_SPEC.md` §6/§8/§11, `AGENTS.md` invariants (full-tile urgency, dark 7-slot rails, no pill-everything, WCAG AA urgency inks, reduced-motion).

**Do NOT change:** any `.ts` logic, stores, router paths, i18n copy, component props/emits, or test selectors used by e2e (check `e2e/tests/` before renaming any class that appears there).

---

### Task 1: Token layer refinement

**Files:**
- Modify: `frontend/src/styles/tokens.css`

**Step 1: Refine raw palette (Layer 1)**

Keep all existing names. Adjust values for finer grading and add new entries:

```css
  /* Warm-cool neutral ramp (canvas family) — warmer, softer */
  --frd-cream-50: #fcfbf7;
  --frd-cream-100: #f7f5ef;
  --frd-cream-200: #f0ede3;
  --frd-cream-300: #e5e0d1;
  --frd-cream-400: #d0c9b7;

  /* Urgency surfaces: softer, more graded tints */
  --frd-coral-500: #e4645a;   /* past date */
  --frd-coral-300: #f6947f;   /* today */
  --frd-amber-400: #f9b45c;   /* 1–2 days */
  --frd-yellow-300: #f7e08c;  /* 3–5 days */
  --frd-stone-100: #f4f2eb;   /* neutral */
```

Re-verify each urgency ink pair stays ≥4.5:1 against its new surface (lightening a surface only raises contrast with the same dark ink — confirm with a contrast checker, adjust ink only if a pair drops below 4.5:1).

Add raw entries for rail gradient and halo:

```css
  --frd-navy-850: #0e2a4a;   /* rail gradient top */
  --frd-halo-blue: 61 123 240; /* selected-slot halo, used with / alpha */
```

**Step 2: Add semantic aliases (Layer 2, append in matching sections)**

```css
  /* Chrome translucency (replaces repeated literals in components) */
  --color-header-bg: rgb(247 245 239 / 0.88);
  --color-nav-bg: rgb(255 255 255 / 0.92);

  /* Dark rail gradient + selection halo */
  --color-rail-gradient: linear-gradient(180deg, var(--frd-navy-850), var(--color-rail));
  --color-halo: rgb(var(--frd-halo-blue) / 0.45);

  /* Urgency accent edges (same-hue 1px inner border per tile) */
  --color-urgency-past-edge: #c94a41;
  --color-urgency-today-edge: #e07a63;
  --color-urgency-soon-edge: #e09a3f;
  --color-urgency-later-edge: #e3cd6d;
  --color-urgency-neutral-edge: var(--frd-cream-300);
```

**Step 3: Upgrade elevation scale**

Replace the four shadow tokens with layered versions:

```css
  --shadow-sm:
    0 1px 2px rgb(var(--frd-shadow-hue) / 0.05),
    0 2px 6px rgb(var(--frd-shadow-hue) / 0.04);
  --shadow-md:
    0 1px 2px rgb(var(--frd-shadow-hue) / 0.05),
    0 4px 12px rgb(var(--frd-shadow-hue) / 0.07),
    0 8px 24px rgb(var(--frd-shadow-hue) / 0.05);
  --shadow-lg:
    0 2px 6px rgb(var(--frd-shadow-hue) / 0.06),
    0 12px 32px rgb(var(--frd-shadow-hue) / 0.12);
  --shadow-overlay:
    0 4px 12px rgb(var(--frd-shadow-hue) / 0.08),
    0 16px 48px rgb(var(--frd-shadow-hue) / 0.16);
  --shadow-token-active:
    0 1px 2px rgb(var(--frd-shadow-hue) / 0.14),
    0 4px 10px rgb(var(--frd-shadow-hue) / 0.14),
    0 0 0 3px rgb(var(--frd-halo-blue) / 0.28);
```

**Step 4: Radii + type additions**

```css
  --radius-card: 14px;  /* cards & tiles (between lg and xl) */

  --font-size-3xl: 2rem; /* 32 — Rescue headline */
  --letter-spacing-display: -0.02em;
```

**Step 5: Verify**

Run: `cd frontend && npm run typecheck && npm run lint` (CSS-only change; must stay green). Also open `http://localhost:5173/dev/tokens` after `npm run dev` and eyeball the ramp.

**Step 6: Commit**

```bash
git add frontend/src/styles/tokens.css
git commit -m "style: refine warm palette, elevation, and semantic tokens"
```

---

### Task 2: Motion infrastructure + page ambience in base.css

**Files:**
- Modify: `frontend/src/styles/base.css`

**Step 1: Page ambience (subtle warm glow on body)**

```css
body {
  /* ...existing declarations... */
  background-color: var(--color-canvas);
  background-image:
    radial-gradient(120% 60% at 50% -10%, rgb(255 252 240 / 0.9), transparent 60%);
  background-attachment: fixed;
}
```

**Step 2: Add motion utilities at the end of base.css**

```css
/* ---------- Entrance motion (UX_SPEC §8: <250ms each, stagger <350ms) ---------- */
@media (prefers-reduced-motion: no-preference) {
  @keyframes frd-rise-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* Apply to direct children of a grid/list: <div class="stagger-in"> */
  .stagger-in > * {
    animation: frd-rise-in var(--duration-slow) var(--ease-out) both;
  }
  .stagger-in > *:nth-child(1) { animation-delay: 0ms; }
  .stagger-in > *:nth-child(2) { animation-delay: 35ms; }
  .stagger-in > *:nth-child(3) { animation-delay: 70ms; }
  .stagger-in > *:nth-child(4) { animation-delay: 105ms; }
  .stagger-in > *:nth-child(5) { animation-delay: 140ms; }
  .stagger-in > *:nth-child(6) { animation-delay: 175ms; }
  .stagger-in > *:nth-child(7) { animation-delay: 210ms; }
  .stagger-in > *:nth-child(n+8) { animation-delay: 245ms; }

  /* Route transitions (used by App.vue) */
  .route-fade-enter-active,
  .route-fade-leave-active {
    transition: opacity var(--duration-base) var(--ease-standard);
  }
  .route-fade-enter-from,
  .route-fade-leave-to { opacity: 0; }

  .route-push-enter-active,
  .route-push-leave-active,
  .route-pop-enter-active,
  .route-pop-leave-active {
    transition: opacity var(--duration-slow) var(--ease-out),
                transform var(--duration-slow) var(--ease-out);
  }
  .route-push-enter-from { opacity: 0; transform: translateX(24px); }
  .route-push-leave-to   { opacity: 0; transform: translateX(-12px); }
  .route-pop-enter-from  { opacity: 0; transform: translateX(-24px); }
  .route-pop-leave-to    { opacity: 0; transform: translateX(12px); }

  /* Sheets & fixed action bars */
  @keyframes frd-sheet-up {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .sheet-up {
    animation: frd-sheet-up var(--duration-slow) var(--ease-out) both;
  }
}
```

The existing `prefers-reduced-motion: reduce` kill-switch already neutralizes all of the above — verify it does.

**Step 3: Verify** — `npm run dev`, navigate; grids with `.stagger-in` rise in (class applied in Task 6). Nothing broken without the class.

**Step 4: Commit** `style: add motion utilities and warm page ambience`

---

### Task 3: Route transitions in App.vue

**Files:**
- Modify: `frontend/src/App.vue`

**Step 1: Direction-aware `<Transition>`**

Track navigation depth: tab routes (`/`, `/rescue`, `/recipes`, `/history`) get `route-fade`; deeper routes get `route-push` on forward navigation and `route-pop` on `router.back()`. Implement:

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppNav from './components/AppNav.vue'

const route = useRoute()
const router = useRouter()
const hideNavigation = computed(() => route.meta.hideNavigation === true)

const TAB_PATHS = ['/', '/rescue', '/recipes', '/history']
const transitionName = ref('route-fade')

router.beforeEach((to, from) => {
  const toTab = TAB_PATHS.includes(to.path)
  const fromTab = TAB_PATHS.includes(from.path)
  if (toTab && fromTab) {
    transitionName.value = 'route-fade'
  } else if (toTab && !fromTab) {
    transitionName.value = 'route-pop' // returning to a tab
  } else {
    transitionName.value = 'route-push' // drilling deeper
  }
})
</script>

<template>
  <div class="app-shell" :class="{ 'app-shell--task': hideNavigation }">
    <AppNav v-if="!hideNavigation" />
    <main class="app-content">
      <router-view v-slot="{ Component }">
        <transition :name="transitionName" mode="out-in">
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>
```

**Step 2: Verify** — click through all 8 routes at 390px and desktop; transitions smooth, no double-render or layout jump (`mode="out-in"` prevents overlap).

**Step 3: Commit** `feat(ui): direction-aware route transitions`

---

### Task 4: AppNav SVG icons + active indicator

**Files:**
- Modify: `frontend/src/components/AppNav.vue`

**Step 1: Replace Unicode glyphs with inline stroke SVGs (24×24, `stroke="currentColor"`, `stroke-width="1.8"`, `fill="none"`, round caps):**

- Storage: rounded-square fridge/box icon (rect + inner shelf line)
- Rescue: life-ring or sparkle-basket icon (circle + inner spokes)
- Recipes: open-book / chef-hat icon
- History: clock icon (circle + hands)

Swap the `symbol` strings in `destinations` for an `icon` key, render via small inline `<svg>` per item (keep `aria-hidden="true"`), e.g.:

```vue
<span class="app-nav__icon" aria-hidden="true">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
       stroke-linecap="round" stroke-linejoin="round">
    <rect x="5" y="3" width="14" height="18" rx="2.5" />
    <path d="M5 10h14" />
  </svg>
</span>
```

**Step 2: Active-state polish**

- `.app-nav__item` gains `transition: color var(--duration-base) var(--ease-standard);`
- Active item: a small top indicator bar on mobile (2px rounded, `--color-primary`, animated via `transform: scaleX` on `router-link-active`) and on desktop a soft primary-tinted background pill (`--color-primary-softer`) instead of color-only — keeps 54px/48px sizes and 44px targets.
- Replace the hardcoded `background: rgb(255 255 255 / 0.96)` with `var(--color-nav-bg)`.

**Step 3: Verify** — all four tabs render crisp icons at 390px + desktop rail; active state visible without color alone (indicator bar); keyboard focus ring intact.

**Step 4: Commit** `feat(ui): coherent SVG nav icons with animated active state`

---

### Task 5: Core component polish

**Files:**
- Modify: `frontend/src/components/AppButton.vue`
- Modify: `frontend/src/components/AppChip.vue`
- Modify: `frontend/src/components/storage-tile/StorageTile.vue`
- Modify: `frontend/src/components/rescue/SelectionRail.vue`
- Modify: `frontend/src/components/recipes/RecipeMatchBelt.vue`

**Step 1: AppButton** — hover: `transform: translateY(-1px)` + `--shadow-md` on primary; press: `scale(0.97)`; transition `--duration-fast` → `--duration-base` with `--ease-standard`. Keep variants/sizes API unchanged.

**Step 2: AppChip** — selected state: add `--shadow-sm`; transition via `--ease-standard`; keep `aria-pressed`.

**Step 3: StorageTile** — apply per-urgency accent edge and inner highlight:

```css
.tile--past    { box-shadow: inset 0 0 0 1px var(--color-urgency-past-edge), inset 0 1px 0 rgb(255 255 255 / 0.35); }
/* …repeat for today/soon/later/neutral with their edge tokens… */
```

Quantity gets `font-variant-numeric: tabular-nums;`. Keep full-tile urgency surfaces and existing class names (e2e may depend on them — check `e2e/tests` first).

**Step 4: SelectionRail + RecipeMatchBelt** — rail background → `var(--color-rail-gradient)` (fallback `var(--color-rail)`); keep `--shadow-inset-rail`. Filled slots: `--shadow-token-active` (includes the halo ring) + `transition: box-shadow var(--duration-base) var(--ease-standard), transform var(--duration-base) var(--ease-pop)`. Belt slot bright/dark state changes transition in place (`opacity`/`filter: saturate()` on the token surface) — never reorder tokens.

**Step 5: Verify** — urgency tiles legible (spot-check contrast), rail/belt animate on selection at 390px.

**Step 6: Commit** `style: polish buttons, chips, tiles, and dark rails`

---

### Task 6: View-level polish + hardcoded-value cleanup

**Files (scoped styles + class additions only):**
- Modify: `frontend/src/views/StorageView.vue`
- Modify: `frontend/src/views/RescueView.vue`
- Modify: `frontend/src/views/ChooseFoodsView.vue`
- Modify: `frontend/src/views/RecipeResultsView.vue`
- Modify: `frontend/src/views/RecipeEditorView.vue`
- Modify: `frontend/src/views/RecipesView.vue`
- Modify: `frontend/src/views/AddFoodView.vue`
- Modify: `frontend/src/components/recipes/StorageIngredientPicker.vue`

**Step 1: Global replacements in every file above**

- `rgb(246 244 238 / 0.94)` → `var(--color-header-bg)`
- `rgb(255 255 255 / 0.96)` → `var(--color-nav-bg)`
- Card radii → `var(--radius-card)`; card shadows → the new `--shadow-sm/md/lg/overlay` as appropriate (sheets/dialogs → `--shadow-overlay`).

**Step 2: RecipeResultsView AI card** — replace hardcoded `#b8cef7` border → `var(--color-primary-soft)`, `#cbd9f3` accents → `var(--color-primary-soft)`/token gradient; keep the existing 145° gradient structure but drive it from `--color-primary-softer` → `--color-surface`.

**Step 3: RescueView headline** — `--font-size-3xl`, `--letter-spacing-display`, weight 700.

**Step 4: Stagger entrances** — add `stagger-in` class to: Storage Use Soon grid + inventory grid (StorageView), picker grid (ChooseFoodsView + StorageIngredientPicker), ingredient grid (RecipeEditorView), source-card list (RecipeResultsView), saved-recipe list (RecipesView). Add `sheet-up` to fixed bottom action bars (AddFoodView, ChooseFoodsView, RecipeEditorView footers) and the picker sheet.

**Step 5: Selection pop** — ChooseFoodsView selected cell: `transition: transform var(--duration-base) var(--ease-pop), box-shadow ...`; `:active`/select uses `--shadow-token-active`.

**Step 6: Verify** — `npm run typecheck && npm run lint` green; walk every screen at 390×844 and ≥880px in both locales; no overflow, sticky bars intact, safe-area respected.

**Step 7: Commit** `style: apply refined tokens and entrance motion across views`

---

### Task 7: Verification pass

**Files:**
- Test: `e2e/tests/` (run existing suite; edit only if a legitimately renamed selector broke — prefer not renaming)

**Step 1:** `cd frontend && npm run typecheck && npm run lint && npm run build` — all green.

**Step 2:** `cd e2e && npx playwright test` — existing suite passes (start backend per e2e README/config first if required; check `e2e/playwright.config.ts` webServer settings).

**Step 3: Visual check** — with `npm run dev` running, capture before/after screenshots at 390×844 and 1280×800 of `/`, `/rescue`, `/rescue/choose`, `/rescue/results`, `/recipes/editor` (use a small Playwright script or the e2e harness) and eyeball: urgency grading, rail halo, stagger timing (<350ms), nav icons.

**Step 4: Reduced-motion + a11y** — emulate `prefers-reduced-motion: reduce` (Playwright `reducedMotion: 'reduce'`) and confirm no entrance animation; keyboard-tab one full flow; spot-check urgency contrast ≥4.5:1.

**Step 5: Commit** `test: verify warm-refinement redesign`

---

## Notes for the executor

- Commit steps require asking the user before each `git commit` (per workspace rules). Stage and propose the message; do not commit silently.
- If an e2e test references a class you want to rename, keep the old class as an additional class instead of renaming.
- All new animation/transition code lives under `prefers-reduced-motion: no-preference` guards.
