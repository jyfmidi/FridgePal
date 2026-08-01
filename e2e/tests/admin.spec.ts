import { expect, test, type Page } from '@playwright/test'
import { signInFreshUser } from '../helpers/auth'

const ADMIN_USERNAME = process.env.FRIDGE_PAL_ADMIN_USERNAME ?? 'admin'
const ADMIN_PASSWORD = process.env.FRIDGE_PAL_ADMIN_PASSWORD ?? 'admin-pass-123'

/**
 * Login as the fixed administrator. Auth endpoints are rate-limited per client
 * address (AUTH_LOGIN_RATE_PER_MINUTE), and the whole e2e suite shares one
 * client address, so bursts occasionally hit 429. The limiter window is 60s:
 * retry long enough to let it drain instead of failing the suite.
 */
async function loginAsAdmin(page: Page) {
  await page.goto('/login')
  for (let attempt = 0; attempt < 9; attempt++) {
    await page.getByLabel('Username', { exact: true }).fill(ADMIN_USERNAME)
    await page.getByLabel('Password', { exact: true }).fill(ADMIN_PASSWORD)
    await page.getByRole('button', { name: 'Log in' }).click()
    try {
      await expect(page).toHaveURL('/', { timeout: 5000 })
      return
    } catch {
      // Rate-limited (or a transient failure): let the window slide and retry.
      await page.waitForTimeout(10_000)
    }
  }
  throw new Error('Admin login kept failing (rate limit or bad credentials)')
}

test.describe('admin console', () => {
  // Login retries can need up to ~90s while the per-address rate window drains.
  test.setTimeout(150_000)

test('admin logs in, sees the admin entry, and lists the Food Library', async ({ page }) => {
  await loginAsAdmin(page)
  await expect(page.getByRole('button', { name: 'Admin' })).toBeVisible()
  await page.getByRole('button', { name: 'Admin' }).click()
  await expect(page).toHaveURL('/admin')
  await expect(page.getByRole('heading', { name: 'Admin' })).toBeVisible()
  // Seeded library entries are listed.
  await expect(page.getByText('Spinach', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add food' })).toBeVisible()
})

test('admin creates a preset food and it appears in Add Food', async ({ page }) => {
  // Both Playwright projects run in parallel against one backend; include a
  // random suffix so the two runs never collide on the derived food key.
  const foodName = `E2E Avocado ${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Admin' }).click()
  await expect(page).toHaveURL('/admin')
  await page.getByRole('button', { name: 'Add food' }).click()
  await expect(page).toHaveURL(/\/admin\/foods\/new/)

  await page.getByLabel('English name').fill(foodName)
  await page.getByLabel('Chinese name').fill('测试牛油果')
  await page.getByLabel('Base unit').selectOption('piece')
  await page.getByLabel('Recommended storage').selectOption('FRIDGE')
  // Pick a curated icon (lemon) instead of Auto.
  await page.getByRole('button', { name: 'Use icon lemon' }).click()
  await page.getByRole('button', { name: 'Save food' }).click()

  // Back on the admin list, the new food is searchable.
  await expect(page).toHaveURL('/admin')
  await page.getByPlaceholder('Search the Food Library').fill('E2E Avocado')
  await expect(page.getByText(foodName, { exact: true })).toBeVisible()

  // Add Food offers the new preset with its chosen icon.
  await page.goto('/add-food')
  await page.getByPlaceholder('Search the Food Library').fill('E2E Avocado')
  await expect(page.getByRole('button', { name: foodName })).toBeVisible()

  // Remove the test food so it never pollutes later runs (soft delete hides it
  // from Add Food and the user-facing library).
  const foodKey = foodName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  const deleted = await page.request.delete(`/api/admin/foods/${foodKey}`)
  expect(deleted.status()).toBe(200)
})

test('admin uploads a custom icon and it renders in Add Food', async ({ page }) => {
  const foodName = `E2E Icon ${Date.now()}-${Math.random().toString(36).slice(2, 6)}`
  const foodKey = foodName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  await loginAsAdmin(page)
  const created = await page.request.post('/api/admin/foods', {
    data: {
      names: { en: foodName },
      category: 'other',
      baseUnit: 'piece',
      recommendedStorage: 'FRIDGE',
      active: true,
      shelfLife: [],
    },
  })
  expect(created.status()).toBe(201)

  await page.goto(`/admin/foods/${foodKey}`)
  const chooserPromise = page.waitForEvent('filechooser')
  await page.getByText('Upload icon').click()
  const chooser = await chooserPromise
  await chooser.setFiles({
    name: 'icon.svg',
    mimeType: 'image/svg+xml',
    buffer: Buffer.from(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" fill="#285f43"/></svg>',
    ),
  })
  await expect(page.getByText('Custom icon uploaded')).toBeVisible()

  // The uploaded icon renders as a Food Token <img> in Add Food.
  await page.goto('/add-food')
  await page.getByPlaceholder('Search the Food Library').fill(foodName)
  const suggestion = page.getByRole('button', { name: foodName })
  await expect(suggestion.locator('img')).toBeVisible()

  const deleted = await page.request.delete(`/api/admin/foods/${foodKey}`)
  expect(deleted.status()).toBe(200)
})

test('settings can be saved and non-admins are blocked from /admin', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Admin' }).click()
  await page.getByRole('tab', { name: 'Settings' }).click()
  await page.getByLabel('Use Soon window (days)').fill('3')
  await page.getByRole('button', { name: 'Save settings' }).click()
  await expect(page.getByText('Settings saved.')).toBeVisible()
  // Restore the default so the demo database stays predictable.
  await page.getByLabel('Use Soon window (days)').fill('5')
  await page.getByRole('button', { name: 'Save settings' }).click()
  await expect(page.getByText('Settings saved.')).toBeVisible()

  // A regular user has no admin entry and cannot reach /admin.
  const fresh = await page.context().newPage()
  await signInFreshUser(fresh)
  await fresh.goto('/admin')
  await expect(fresh).toHaveURL('/')
  await expect(fresh.getByRole('button', { name: 'Admin' })).toHaveCount(0)
})
})
