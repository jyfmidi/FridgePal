# Food Token Recognition Fixes Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace four ambiguous Food Token subjects, correct the fish direction, and verify the revised silhouettes at every supported small-icon size.

**Architecture:** Keep the registry, keys, Vue component factory, and shared primitives unchanged. Replace only the affected definition arrays in `proteins.ts` and `legacy.ts`, and make the developer size ramp a focused review surface for the six corrected keys.

**Tech Stack:** Vue 3, TypeScript, deterministic 48×48 SVG definitions, Playwright, ESLint, vue-tsc, Vite.

---

### Task 1: Add the failing corrected-icon review contract

**Files:**
- Modify: `e2e/tests/food-token-catalog.spec.ts`

**Step 1: Write the failing browser contract**

Add a second test that signs in, opens `/dev/tokens`, locates the `Size ramp` section, and expects four rendered instances each for `pork`, `beef`, `lamb`, `duck`, `fish`, and `pasta`:

```ts
test('the corrected recognition set is exposed at every review size', async ({ page }) => {
  await signInFreshUser(page)
  await page.goto('/dev/tokens')

  const sizeRamp = page.locator('section', {
    has: page.getByRole('heading', { name: 'Size ramp' }),
  })

  for (const key of ['pork', 'beef', 'lamb', 'duck', 'fish', 'pasta']) {
    await expect(sizeRamp.getByRole('img', { name: key })).toHaveCount(4)
  }
})
```

**Step 2: Run the test and verify RED**

Run from `e2e/`:

```bash
env PATH=/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin:/usr/bin:/bin \
  /Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node \
  node_modules/@playwright/test/cli.js test tests/food-token-catalog.spec.ts \
  --project desktop-chrome --config playwright.config.ts
```

Expected: FAIL because the current size ramp does not contain the complete corrected set.

### Task 2: Replace the ambiguous SVG subjects

**Files:**
- Modify: `frontend/src/components/food-token/icons/catalog/proteins.ts`
- Modify: `frontend/src/components/food-token/icons/catalog/legacy.ts`
- Modify: `frontend/src/views/DevTokens.vue`

**Step 1: Implement the approved animal silhouettes**

- Replace `pork` with a side-profile pig: round pink body, head/snout, short legs, ear, and curled tail.
- Replace `beef` with a side-profile cow: broad red-brown body, head, horns, legs, and tail.
- Replace `lamb` with a side-profile sheep: scalloped cream wool body with dark face and legs.
- Replace `duck` with a side-profile duck: orange-brown body, raised neck/head, flat bill, wing, and webbed feet.
- Leave `chicken-breast` and `chicken-thigh` unchanged.
- Reverse and redraw `fish` so its head, eye, and gill are on the left and its tail is on the right.

**Step 2: Implement the spaghetti bundle**

Replace the package-like `pasta` definition with a slightly angled bundle of dry spaghetti: one warm-yellow bundle silhouette, visible parallel strand lines, flat ends, and one darker tie band. Remove now-unused legacy primitive imports.

**Step 3: Update the size-ramp review set**

Set:

```ts
const sizeSampleKeys = ['pork', 'beef', 'lamb', 'duck', 'fish', 'pasta']
```

**Step 4: Run focused static checks**

Run from `frontend/`:

```bash
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/eslint/bin/eslint.js src/components/food-token/icons/catalog src/views/DevTokens.vue
/Users/jyfmidi/.nvm/nvm/versions/node/v24.18.1/bin/node node_modules/vue-tsc/bin/vue-tsc.js --noEmit -p tsconfig.json
```

Expected: PASS.

**Step 5: Run the focused browser contract and verify GREEN**

Repeat the Task 1 Playwright command. Expected: both catalog tests PASS.

### Task 3: Visual QA, regression verification, and delivery

**Files:**
- Update: `docs/visuals/food-token-library.png`
- Update if needed: `docs/FOOD_TOKEN_ICON_GUIDE.md`

**Step 1: Inspect the real developer board**

Capture the complete light-surface registry and the corrected 24/32/48/64 px ramp. Confirm each animal is recognizable without its label, the fish eye is at the head, and pasta reads as dry spaghetti.

**Step 2: Apply at most one targeted geometry correction per failed subject**

If a subject fails, change only its definition, repeat focused lint/typecheck, and recapture the board. If three correction attempts fail, stop and reconsider the silhouette architecture with the user.

**Step 3: Run final verification**

Run frontend ESLint, vue-tsc, Vite production build, `git diff --check`, and the complete Playwright mobile/desktop suite. Expected: all PASS.

**Step 4: Commit**

```bash
git add e2e/tests/food-token-catalog.spec.ts \
  frontend/src/components/food-token/icons/catalog/proteins.ts \
  frontend/src/components/food-token/icons/catalog/legacy.ts \
  frontend/src/views/DevTokens.vue \
  docs/visuals/food-token-library.png
git commit -m "fix: improve Food Token recognition"
```
