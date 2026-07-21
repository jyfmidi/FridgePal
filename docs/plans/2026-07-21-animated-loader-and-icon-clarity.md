# Animated Loader and Icon Clarity Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a continuously looping Fridge Pal character loader for initial and long recipe-search waits, and make History Storage event icons and food identity immediately understandable.

**Architecture:** Build one inline-SVG `FridgePalLoader` with page and compact variants so the existing mark can twist, anticipate, hop, and settle as a single character. Drive initial visibility from app-level inventory hydration and recipe visibility from the existing Rescue search state. Keep functional icons in `AppIcon`, then map History events to explicit semantic icons and forward canonical food keys to the shared Food Token registry.

**Tech Stack:** Vue 3, TypeScript, scoped CSS animations, vue-i18n, Playwright, Vite.

---

### Task 1: Lock the loader behavior in browser tests

**Files:**
- Create: `e2e/tests/loader-and-history-icons.spec.ts`

**Step 1: Write the failing initial-loader test**

Mock `GET /api/storage` with a 500 ms delay, open `/`, and assert that a page loader appears after the anti-flicker delay and disappears after hydration:

```ts
test('initial hydration shows the looping Fridge Pal character', async ({ page }) => {
  await page.route('**/api/storage', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500))
    await route.fulfill({ json: { useSoon: [], inventory: [] } })
  })
  await page.goto('/')
  const loader = page.getByRole('status', { name: 'Loading Fridge Pal…' })
  await expect(loader).toBeVisible()
  await expect(loader.locator('[data-motion="wiggle-hop"]')).toBeVisible()
  await expect(loader).toBeHidden()
})
```

Use a response-controlled promise if Playwright navigation timing makes the fixed delay race-prone.

**Step 2: Write the failing reduced-motion test**

Emulate `reducedMotion: 'reduce'`, delay Storage, and assert that the character has no named CSS animation while the status text remains visible.

**Step 3: Write the failing History identity test**

Mock Storage and History with a `CHECK_IN` event for `spinach`. Assert that the entry exposes `data-event-icon="stock-in"`, displays the localized `Added` label, and renders the curated spinach SVG rather than `.food-token__monogram`.

**Step 4: Run the focused test and verify failure**

Run:

```bash
cd e2e && npx playwright test tests/loader-and-history-icons.spec.ts --project=mobile-chrome
```

Expected: FAIL because `FridgePalLoader`, the semantic event icon hook, and History food-key forwarding do not exist.

**Step 5: Commit the failing contract**

```bash
git add e2e/tests/loader-and-history-icons.spec.ts
git commit -m "test: define loader and history icon behavior"
```

### Task 2: Build the looping Fridge Pal character

**Files:**
- Create: `frontend/src/components/FridgePalLoader.vue`
- Modify: `frontend/src/i18n/index.ts`

**Step 1: Create the component markup**

Define props `variant?: 'page' | 'compact'` and `label: string`. Render a `role="status"` container with `:aria-label="label"`, an inline `64 × 80` SVG that preserves the current coral logo geometry, and visible localized status text. Put the body shapes inside a character group with `data-motion="wiggle-hop"`; use subgroups for the upper door, lower door, eyes, and handles so they can follow the body with slight lag.

**Step 2: Implement the approved continuous loop**

Under `@media (prefers-reduced-motion: no-preference)`, animate the character group with a 1.65 s infinite keyframe sequence:

```css
@keyframes fridge-pal-wiggle-hop {
  0%, 100% { transform: translateY(0) rotate(0deg) scale(1); }
  12% { transform: translateY(0) rotate(-4deg) scaleX(0.98); }
  24% { transform: translateY(0) rotate(4deg) scaleX(0.98); }
  36% { transform: translateY(2px) rotate(0deg) scale(1.04, 0.94); }
  52% { transform: translateY(-8px) rotate(0deg) scale(0.98, 1.03); }
  68% { transform: translateY(0) rotate(0deg) scale(1.04, 0.94); }
  80% { transform: translateY(-2px) rotate(0deg) scale(0.99, 1.01); }
}
```

Set `transform-box: fill-box` and a bottom-center transform origin. Add only a subtle delayed handle/door follow-through; do not animate the doors as opening.

**Step 3: Add both locale strings**

Add `loading.initial` as `Loading Fridge Pal…` / `Fridge Pal 正在准备中…`. Continue using `recipeResults.loading` for recipe-search status.

**Step 4: Run static verification**

Run:

```bash
cd frontend && npm run lint && npm run typecheck
```

Expected: PASS.

**Step 5: Commit the character component**

```bash
git add frontend/src/components/FridgePalLoader.vue frontend/src/i18n/index.ts
git commit -m "feat: add looping Fridge Pal loader"
```

### Task 3: Integrate page and recipe-search loader variants

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/views/RescueView.vue`

**Step 1: Add delayed initial hydration state**

In `App.vue`, import `onMounted`/`onBeforeUnmount` and `FridgePalLoader`. Start one app-level `hydrateFromServer()` call, but reveal the page loader only after 150 ms. Clear the timer and release the initial state in `finally`, including server failure so the existing local-only UI remains usable.

Keep the router view mounted only after the initial hydration promise settles to avoid duplicate initial fetches and a flash of stale demo inventory. Render:

```vue
<FridgePalLoader
  v-if="showInitialLoader"
  class="app-initial-loader"
  variant="page"
  :label="t('loading.initial')"
/>
```

Do not impose a minimum display time; a completed request should release the UI immediately.

**Step 2: Replace the Rescue spinner**

Replace `.rescue-loading-overlay__spinner` with the compact `FridgePalLoader`, passing `t('recipeResults.loading')`. Preserve the selected-food rail behind the overlay and keep the existing error/Retry behavior.

**Step 3: Remove obsolete spinner CSS**

Delete the local `spin` keyframe and spinner border styles from `RescueView.vue`. Keep overlay layout and backdrop styling.

**Step 4: Re-run focused loader tests**

Run:

```bash
cd e2e && npx playwright test tests/loader-and-history-icons.spec.ts -g "loader|hydration" --project=mobile-chrome
```

Expected: PASS for normal and reduced-motion loader tests.

**Step 5: Commit integration**

```bash
git add frontend/src/App.vue frontend/src/views/RescueView.vue
git commit -m "feat: use branded loaders for meaningful waits"
```

### Task 4: Clarify History Storage event icons

**Files:**
- Modify: `frontend/src/components/AppIcon.vue`
- Modify: `frontend/src/views/HistoryView.vue`

**Step 1: Add explicit semantic icons**

Extend `AppIconName` and its SVG registry with `stock-in`, `consume`, `move`, and `cooking-pot`. Use these concepts:

- `stock-in`: a small Storage box/tray with one downward arrow and plus.
- `consume`: a simple fork-and-spoon pair or one clear item-leaving mark; it must not be a bare minus.
- `move`: one item between two location outlines with a single direction arrow; it must not resemble Undo.
- `cooking-pot`: a shallow pot with lid and two short steam strokes.

Simplify `undo` to one curved return arrow. Retain existing icon names needed by other screens until the audit proves they are unused.

**Step 2: Update History mapping and visual hooks**

Map events as follows:

```ts
const eventIconMap = {
  CHECK_IN: 'stock-in',
  EDIT: 'edit',
  MOVE: 'move',
  MANUAL_CONSUMPTION: 'consume',
  COOKING: 'cooking-pot',
  DISCARD: 'trash',
  REVERSAL: 'undo',
} satisfies Record<HistoryEvent['eventType'], AppIconName>
```

Add `:data-event-icon="eventIconMap[event.eventType]"` to the icon wrapper and event-type modifier classes for restrained semantic tints. Keep the visible localized event label.

**Step 3: Restore curated food identity**

For non-cooking entries, render:

```vue
<FoodToken :food-key="event.foodKey" :name="getFoodName(event)" :size="28" />
```

Keep cooking events' existing `foodKey` forwarding. Correct any duplicate template branch encountered in the edited History block without changing History behavior.

**Step 4: Run the focused History test**

Run:

```bash
cd e2e && npx playwright test tests/loader-and-history-icons.spec.ts -g "History" --project=mobile-chrome
```

Expected: PASS.

**Step 5: Commit History clarity changes**

```bash
git add frontend/src/components/AppIcon.vue frontend/src/views/HistoryView.vue
git commit -m "fix: clarify history storage event icons"
```

### Task 5: Audit, responsive QA, and final verification

**Files:**
- Modify if required: `frontend/src/components/AppIcon.vue`
- Modify if required: `frontend/src/components/AppNav.vue`
- Modify if required: `frontend/src/views/StorageItemView.vue`
- Modify if required: `frontend/src/views/RecipeEditorView.vue`
- Verify: `frontend/src/components/FridgePalLoader.vue`
- Verify: `frontend/src/views/HistoryView.vue`

**Step 1: Audit icon semantics**

Search every `AppIcon` use. Confirm each consequential icon has nearby localized text or an accessible label, one icon name does not represent unrelated actions, and icon paths follow the shared rounded line style. Make only direct clarity fixes; do not redesign the whole navigation or add a dependency.

**Step 2: Run frontend checks**

Run:

```bash
cd frontend && npm run lint && npm run typecheck && npm run build
```

Expected: all PASS.

**Step 3: Run browser verification on both viewports**

Run:

```bash
cd e2e && npx playwright test tests/loader-and-history-icons.spec.ts tests/smoke.spec.ts
```

Expected: PASS on mobile-chrome and desktop-chrome.

**Step 4: Visually inspect the character and event entries**

At approximately `390 × 844` and `1440 × 900`, confirm:

- the logo clearly twists twice and jumps once in a continuous loop;
- the hop stays within its loading surface and status copy does not jump;
- compact search loading preserves context;
- reduced motion is static;
- History icons read as distinct actions and curated Food Tokens are recognizable;
- Chinese copy fits without clipping at 200% zoom.

**Step 5: Commit any final direct audit fixes**

```bash
git add frontend/src/components/AppIcon.vue frontend/src/components/AppNav.vue frontend/src/views/StorageItemView.vue frontend/src/views/RecipeEditorView.vue
git commit -m "fix: normalize functional icon semantics"
```

Skip this commit when the audit requires no code changes.
