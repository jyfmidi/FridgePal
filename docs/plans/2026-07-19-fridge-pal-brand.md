# Fridge Pal Brand Rename and Logo Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rename the user-facing product to Fridge Pal and ship a standalone coral refrigerator-agent SVG mark in the application chrome.

**Architecture:** Keep the logo as a deterministic public SVG asset with no embedded text, then reference it from the global page header and favicon. Rename canonical product copy and runtime metadata while preserving legacy persistence, database, Docker-volume, and operating-user identifiers whose renaming could hide existing user data or break upgrades.

**Tech Stack:** Vue 3, TypeScript, Vite public assets, vue-i18n, FastAPI, pytest, Playwright, SVG.

---

### Task 1: Lock the new product identity in tests

**Files:**
- Modify: `e2e/tests/smoke.spec.ts:3-6`
- Modify: `backend/tests/integration/test_boot.py:7-12`

**Step 1: Write the failing browser smoke contract**

Replace the old visible-wordmark assertion with:

```ts
test('Fridge Pal title and standalone brand mark render', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle('Fridge Pal')
  await expect(page.getByRole('img', { name: 'Fridge Pal' })).toBeVisible()
})
```

**Step 2: Write the failing backend metadata contract**

Add:

```python
def test_application_uses_fridge_pal_title() -> None:
    assert app.title == "Fridge Pal"
```

**Step 3: Run the focused tests and verify failure**

Run: `cd backend && .venv/bin/pytest tests/integration/test_boot.py -q`

Expected: FAIL because the FastAPI title is still `Fridgital`.

Run: `cd e2e && npx playwright test tests/smoke.spec.ts`

Expected: FAIL because the document title and global-header image do not yet exist.

**Step 4: Commit the failing tests**

```bash
git add backend/tests/integration/test_boot.py e2e/tests/smoke.spec.ts
git commit -m "test: define Fridge Pal brand identity"
```

### Task 2: Create and integrate the standalone refrigerator mark

**Files:**
- Create: `frontend/public/brand/fridge-pal-mark.svg`
- Modify: `frontend/index.html:3-7`
- Modify: `frontend/src/components/AppPageHeader.vue:8-65`
- Modify: `frontend/src/i18n/index.ts:9,103`

**Step 1: Create the SVG asset**

Create a `64 × 64` viewBox containing two stacked coral door blocks. Use a shorter upper door, taller lower door, two white rectangular eyes, a transparent door gap, and one short dark-coral handle on the lower door. Keep the SVG free of text, gradients, shadows, strokes, and blue.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path fill="#F47B65" d="M12 5h40a6 6 0 0 1 6 6v17H6V11a6 6 0 0 1 6-6Z"/>
  <path fill="#EE6A56" d="M6 32h52v21a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V32Z"/>
  <rect width="6" height="10" x="19" y="14" fill="#FFF" rx="1"/>
  <rect width="6" height="10" x="39" y="14" fill="#FFF" rx="1"/>
  <rect width="4" height="12" x="48" y="38" fill="#B84739" rx="2"/>
</svg>
```

**Step 2: Integrate favicon and document title**

Add `<link rel="icon" href="/brand/fridge-pal-mark.svg" type="image/svg+xml">` and set `<title>Fridge Pal</title>`.

**Step 3: Replace the global text wordmark with the standalone mark**

Render:

```vue
<img
  class="app-page-header__brand"
  src="/brand/fridge-pal-mark.svg"
  :alt="t('app.title')"
  width="36"
  height="36"
>
```

Keep the existing three-column header hierarchy. Size the mark to `36 × 36px` on mobile and `40 × 40px` on desktop; use `object-fit: contain` and no decorative filter.

**Step 4: Rename both locale title values**

Set `app.title` to `Fridge Pal` for English and Simplified Chinese. Do not localize the product name.

**Step 5: Run the frontend checks**

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`

Expected: all commands PASS and the SVG is copied to `dist/brand/fridge-pal-mark.svg`.

**Step 6: Re-run the browser smoke test**

Run: `cd e2e && npx playwright test tests/smoke.spec.ts`

Expected: PASS.

**Step 7: Commit the mark and header integration**

```bash
git add frontend/public/brand/fridge-pal-mark.svg frontend/index.html frontend/src/components/AppPageHeader.vue frontend/src/i18n/index.ts
git commit -m "feat: add Fridge Pal refrigerator mark"
```

### Task 3: Rename canonical product and runtime surfaces

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `.env.example`
- Modify: `task_plan.md`
- Modify: `docs/PRODUCT_REQUIREMENTS.md`
- Modify: `docs/DOMAIN_AND_AI_CONTRACTS.md`
- Modify: `docs/UX_SPEC.md`
- Modify: `docs/IMPLEMENTATION_PLAN.md`
- Modify: `docs/DEPLOYMENT.md`
- Modify: `docs/plans/2026-07-18-warm-refinement-ui-plan.md`
- Modify: `docs/plans/2026-07-19-canonical-inventory-units-design.md`
- Modify: `docs/plans/2026-07-19-docker-compose-deployment-design.md`
- Modify: `docs/plans/2026-07-19-docker-compose-deployment.md`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/infrastructure/db/base.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/tests/integration/test_static_spa.py`
- Modify: `frontend/src/styles/base.css`
- Modify: `frontend/src/styles/tokens.css`
- Modify: `frontend/src/components/recipes/CookingSheet.vue`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `e2e/package.json`
- Modify: `e2e/package-lock.json`

**Step 1: Rename canonical and user-facing prose**

Replace product-name uses of `Fridgital` with `Fridge Pal`. Update `UI-CMP-06` to describe the standalone Fridge Pal mark rather than a text wordmark. Preserve requirement IDs, behavior contracts, paths, and the product's existing scope.

**Step 2: Rename runtime metadata**

Set the FastAPI title and product-facing Python docstrings to `Fridge Pal`. Rename package distribution metadata to `fridge-pal-backend`, `fridge-pal-frontend`, and `fridge-pal-e2e` together with lockfile root metadata.

**Step 3: Preserve compatibility-sensitive internal identifiers**

Do not rename these existing identifiers:

- localStorage keys beginning `fridgital.`;
- the default local SQLite filename `fridgital.db`;
- existing Docker Compose project, database, volume, and Linux user identifiers using `fridgital`.

Label them as stable legacy internal identifiers where documentation could otherwise imply they are the product name. This prevents existing browser, database, and Docker data from appearing to disappear after a brand-only update.

**Step 4: Update static-serving fixture text**

Change the fixture title and assertion from `Fridgital SPA` to `Fridge Pal SPA` without altering the fallback-route behavior under test.

**Step 5: Run backend and frontend verification**

Run: `cd backend && .venv/bin/pytest tests/integration/test_boot.py tests/integration/test_static_spa.py -q`

Expected: PASS.

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`

Expected: PASS.

**Step 6: Audit remaining old-name literals**

Run: `rg -n --hidden -S "Fridgital|fridgital" -g '!node_modules' -g '!.git' .`

Expected: remaining lowercase matches are only explicitly preserved compatibility identifiers or historical deployment evidence; title-case matches exist only in the approved rename design/plan where the former name must be stated.

**Step 7: Commit the rename**

```bash
git add AGENTS.md README.md .env.example task_plan.md docs backend frontend/package.json frontend/package-lock.json e2e/package.json e2e/package-lock.json
git commit -m "chore: rename product to Fridge Pal"
```

### Task 4: Visual and release verification

**Files:**
- Verify: `frontend/public/brand/fridge-pal-mark.svg`
- Verify: `frontend/src/components/AppPageHeader.vue`
- Verify: repository working tree

**Step 1: Render the SVG for visual inspection**

Render the production SVG to a PNG preview at a large size and inspect it at both full scale and a simulated 24 px size. Confirm that the two white shapes read only as eyes and the dark-coral lower-door handle does not resemble another eye.

**Step 2: Inspect representative responsive headers**

Check Storage at approximately `390 × 844` and one desktop viewport. Confirm the mark is crisp, the centered page title remains centered, actions do not overlap, and task headers remain unbranded.

**Step 3: Run the fresh release checks**

Run: `cd backend && .venv/bin/pytest tests/integration/test_boot.py tests/integration/test_static_spa.py -q`

Run: `cd frontend && npm run lint && npm run typecheck && npm run build`

Run: `cd e2e && npx playwright test tests/smoke.spec.ts`

Expected: all checks PASS.

**Step 4: Confirm a clean scope**

Run: `git status --short && git diff --check`

Expected: only intended brand changes before the final commit; no whitespace errors.
