# Common Food Icon Library Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the approved 70-food Bold Pantry SVG family to Fridge Pal's curated Food Token registry while retaining `rice` and `pasta` as compatibility keys.

**Architecture:** Keep `FoodToken.vue` unchanged. Define typed SVG primitive arrays in category modules, turn each definition into an ordinary Vue component with a small render-function factory, and expose 72 components through the existing `foodIcons` registry. The database and demo inventory remain unchanged; admins opt into new `visualKey` values through the existing editor.

**Tech Stack:** Vue 3, TypeScript, SVG, Playwright, ESLint, vue-tsc, Vite.

---

### Task 1: Add the registry and admin RED contracts

**Files:**
- Create: `e2e/tests/food-token-catalog.spec.ts`
- Modify: `e2e/tests/admin.spec.ts`

**Step 1: Write the failing development-showcase contract**

Create a browser test that signs in, visits `/dev/tokens`, scopes to the light-surface icon grid, and expects exactly 72 cells. Assert that representative new keys from all categories—`bok-choy`, `dragon-fruit`, `chicken-thigh`, and `dried-tofu`—exist and contain `.food-token__icon`/`svg`, with no `.food-token__monogram`.

```ts
test('the curated Food Token registry exposes the complete household catalog', async ({ page }) => {
  await signInFreshUser(page)
  await page.goto('/dev/tokens')

  const grid = page.locator('.dev-tokens__grid--light')
  await expect(grid.locator('.dev-tokens__cell')).toHaveCount(72)

  for (const key of ['bok-choy', 'dragon-fruit', 'chicken-thigh', 'dried-tofu']) {
    const cell = grid.locator('figure', { hasText: key })
    await expect(cell.locator('svg.food-token__icon')).toBeVisible()
    await expect(cell.locator('.food-token__monogram')).toHaveCount(0)
  }
})
```

**Step 2: Run the showcase test and verify RED**

Run from `e2e/` with the NVM Node runtime first on `PATH`:

```bash
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  node_modules/@playwright/test/cli.js test tests/food-token-catalog.spec.ts \
  --config playwright.config.ts --project=desktop-chrome
```

Expected: FAIL because the current light grid has 16 cells instead of 72.

**Step 3: Extend the existing admin test with a new visual key**

Change the create-food test to choose `apple` rather than `lemon` and retain the existing end-to-end assertion that the created preset appears in Add Food.

```ts
await page.getByRole('button', { name: 'Use icon apple' }).click()
```

**Step 4: Run the focused admin test and verify RED**

Run:

```bash
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  node_modules/@playwright/test/cli.js test tests/admin.spec.ts \
  --config playwright.config.ts --project=desktop-chrome --grep "admin creates a preset food"
```

Expected: FAIL because `Use icon apple` does not exist.

### Task 2: Add the typed SVG catalog foundation

**Files:**
- Create: `frontend/src/components/food-token/icons/catalog/types.ts`
- Create: `frontend/src/components/food-token/icons/catalog/palette.ts`
- Create: `frontend/src/components/food-token/icons/catalog/primitives.ts`
- Create: `frontend/src/components/food-token/icons/createFoodIcon.ts`

**Step 1: Define the primitive contract**

Define a narrow union for `path`, `circle`, `ellipse`, `rect`, `line`, `polyline`, and `polygon`. SVG attributes accept strings or numbers. Definitions are readonly arrays.

```ts
export type FoodIconElement = Readonly<{
  tag: 'path' | 'circle' | 'ellipse' | 'rect' | 'line' | 'polyline' | 'polygon'
  attrs: Readonly<Record<string, string | number>>
}>

export type FoodIconDefinition = readonly FoodIconElement[]
```

**Step 2: Add shared palette tokens**

Export semantically named local colors for greens, red/orange/yellow produce, purple produce, neutral roots/fungi, meat, dairy, and aquatic foods. Keep each icon to two or three dominant fills even when palette modules contain more colors.

**Step 3: Add concise primitive helpers**

Provide helpers such as `path(d, fill, attrs?)`, `circle(cx, cy, r, fill, attrs?)`, and equivalent helpers for the remaining primitive tags. Helpers must return `FoodIconElement` and never inject background shapes, gradients, filters, masks, text, or external references.

**Step 4: Add the Vue component factory**

Use `defineComponent` and `h` to render one `48 × 48` SVG with `fill="none"`, `aria-hidden="true"`, and `focusable="false"`. Render each primitive from the definition with a stable key.

```ts
export function createFoodIcon(name: string, definition: FoodIconDefinition): Component {
  return defineComponent({
    name,
    setup: () => () => h('svg', {
      viewBox: '0 0 48 48',
      fill: 'none',
      xmlns: 'http://www.w3.org/2000/svg',
      'aria-hidden': 'true',
      focusable: 'false',
    }, definition.map((element, index) => h(element.tag, { ...element.attrs, key: index }))),
  })
}
```

**Step 5: Run focused lint and typecheck**

Run from `frontend/`:

```bash
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/eslint/bin/eslint.js src/components/food-token/icons
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/vue-tsc/bin/vue-tsc.js --noEmit -p tsconfig.json
```

Expected: PASS. The browser contracts remain RED because definitions are not registered yet.

### Task 3: Generate all category definitions and register 72 keys

**Files:**
- Create: `frontend/src/components/food-token/icons/catalog/vegetables.ts`
- Create: `frontend/src/components/food-token/icons/catalog/fruits.ts`
- Create: `frontend/src/components/food-token/icons/catalog/proteins.ts`
- Create: `frontend/src/components/food-token/icons/catalog/chilled.ts`
- Create: `frontend/src/components/food-token/icons/catalog/legacy.ts`
- Modify: `frontend/src/components/food-token/icons/index.ts`

**Step 1: Implement the 38 vegetable/fungi/aromatic definitions**

Export a typed record with exactly the 38 approved keys in the design document. Use the Bold Pantry constraints: centered 4 px safe area, one dominant silhouette, two or three main fills, and only recognition-critical small strokes.

**Step 2: Implement the 18 fruit definitions**

Use strong outer silhouettes and one cut face only for recognition-dependent foods such as watermelon, kiwi, dragon fruit, and cantaloupe. Keep orange and mandarin distinct through pose/leaf/segment cues rather than labels.

**Step 3: Implement the 10 meat/egg/aquatic definitions**

Use abstract clean cuts with no blood or realistic butchery. Keep chicken breast, chicken thigh, pork, beef, lamb, and duck distinct through silhouette and local color. Fish, shrimp, and crab must remain readable at 24 px.

**Step 4: Implement the 4 soy/chilled definitions**

Use ingredient silhouettes for tofu and dried tofu; use generic unbranded containers for milk and yogurt.

**Step 5: Implement compatibility-only rice and pasta definitions**

Redraw `rice` and `pasta` in the same palette/lighting contract so old user data does not introduce a mixed visual family. Do not add either concept to the approved 70-food list or seed catalog.

**Step 6: Replace the registry assembly**

Merge the five category records, create one Vue component per key with `createFoodIcon`, and export the result as `foodIcons`. Preserve the public `Record<string, Component>` contract.

Add a development assertion/type constraint so duplicate or omitted source keys are visible during compilation. The final registry must contain exactly 72 unique keys.

**Step 7: Run the two focused browser contracts and verify GREEN**

Run the exact Task 1 commands. Expected: both tests PASS; the showcase reports 72 icons and the admin can choose `apple`.

**Step 8: Commit the icon catalog slice**

Stage only the catalog files, registry, and two browser tests. Commit:

```bash
git commit -m "feat: add common Food Token icon library"
```

### Task 4: Improve the visual QA surface and document reproduction

**Files:**
- Modify: `frontend/src/views/DevTokens.vue`
- Create: `docs/FOOD_TOKEN_ICON_GUIDE.md`
- Modify: `docs/UX_SPEC.md`

**Step 1: Expand the size-ramp representatives**

Use at least one leafy vegetable, pale vegetable, fruit, meat, aquatic food, and chilled package in the size ramp. Keep all registry keys visible on both light and neutral tray surfaces.

**Step 2: Write the reusable guide**

Move the approved reusable prompt, negative constraints, viewBox/safe-area rules, packaging rule, palette/lighting contract, subject-clause examples, naming rules, and QA checklist into `docs/FOOD_TOKEN_ICON_GUIDE.md`.

**Step 3: Link the canonical UX contract**

Add one line under `UI-CMP-01` in `docs/UX_SPEC.md` stating that production construction and future-generation guidance live in `docs/FOOD_TOKEN_ICON_GUIDE.md`. Do not duplicate the full contract in UX Spec.

**Step 4: Run lint, typecheck, and build**

Run from `frontend/`:

```bash
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/eslint/bin/eslint.js .
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/vue-tsc/bin/vue-tsc.js --noEmit -p tsconfig.json
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/vite/bin/vite.js build
```

Expected: all commands exit 0.

### Task 5: Visual QA, regression verification, and cleanup

**Files:**
- Modify as needed: `frontend/src/components/food-token/icons/catalog/*.ts`
- Delete after registry migration: superseded per-icon Vue files under `frontend/src/components/food-token/icons/Icon*.vue`

**Step 1: Inspect the complete registry at desktop width**

Open `/dev/tokens` at 1440 × 900. Inspect both light and tray grids for clipping, duplicate silhouettes, inconsistent lighting, thin details, pale-food contrast, and accidental badge-like compositions.

**Step 2: Inspect representative icons at mobile token sizes**

Inspect 24/32/48/64 px rows, including `bok-choy`, `cauliflower`, `dragon-fruit`, `chicken-thigh`, `fish`, and `milk`. Make one targeted SVG correction per issue and re-check.

**Step 3: Inspect the admin picker**

Log in as admin, open a food editor, select `apple`, and confirm the 44 px picker preview remains recognizable and selected state is clear. Do not save or mutate an existing preset during manual QA.

**Step 4: Remove superseded icon components**

After the data-driven registry is verified, delete old unreferenced `Icon*.vue` files so the repository has one production Food Token source of truth. This deletion is recoverable through Git history.

**Step 5: Run the complete verification gate**

Run:

```bash
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node frontend/node_modules/eslint/bin/eslint.js frontend e2e/tests/food-token-catalog.spec.ts e2e/tests/admin.spec.ts
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node frontend/node_modules/vue-tsc/bin/vue-tsc.js --noEmit -p frontend/tsconfig.json
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node frontend/node_modules/vite/bin/vite.js build --config frontend/vite.config.ts
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  e2e/node_modules/@playwright/test/cli.js test \
  --config e2e/playwright.config.ts
git diff --check
```

Expected: ESLint, vue-tsc, Vite build, all mobile/desktop browser tests, and whitespace validation pass with zero failures.

**Step 6: Commit documentation and polish**

Stage the guide, UX reference, showcase improvements, SVG corrections, and old-file removals. Commit:

```bash
git commit -m "docs: add Food Token reproduction guide"
```
