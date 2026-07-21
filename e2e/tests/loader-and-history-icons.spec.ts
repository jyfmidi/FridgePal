import { expect, test, type Page, type Route } from '@playwright/test'

const emptyStorage = {
  useSoon: [],
  inventory: [],
}

function controlledStorageResponse(page: Page) {
  let releaseResponse!: () => void
  let requestCount = 0
  const responseReleased = new Promise<void>((resolve) => {
    releaseResponse = resolve
  })

  return {
    get requestCount() {
      return requestCount
    },
    release: releaseResponse,
    install: () => page.route('**/api/storage', async (route: Route) => {
      requestCount += 1
      await responseReleased
      await route.fulfill({ json: emptyStorage })
    }),
  }
}

test('initial hydration shows the looping Fridge Pal character', async ({ page }) => {
  const storage = controlledStorageResponse(page)
  await storage.install()

  const navigation = page.goto('/')

  const loader = page.getByRole('status').filter({ hasText: 'Loading Fridge Pal…' })
  await expect(loader).toBeVisible()
  const character = loader.locator('[data-motion="wiggle-hop"]')
  await expect(character).toBeVisible()
  const mark = loader.locator('.fridge-pal-loader__mark')
  const label = loader.locator('.fridge-pal-loader__label')
  const markToLabelGap = await loader.evaluate((_, elements) => {
    const markBounds = elements.mark.getBoundingClientRect()
    const labelBounds = elements.label.getBoundingClientRect()
    return labelBounds.top - markBounds.bottom
  }, { mark: await mark.elementHandle(), label: await label.elementHandle() })
  expect(markToLabelGap).toBeLessThanOrEqual(32)

  storage.release()
  await navigation
  await expect(loader).toBeHidden()
  await expect.poll(() => storage.requestCount).toBe(1)
})

test('reduced motion keeps the hydration status without animating the character', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  const storage = controlledStorageResponse(page)
  await storage.install()

  const navigation = page.goto('/')

  const loader = page.getByRole('status').filter({ hasText: 'Loading Fridge Pal…' })
  await expect(loader).toBeVisible()
  const character = loader.locator('[data-motion="wiggle-hop"]')
  await expect(character).toBeVisible()
  await expect(character).toHaveCSS('animation-name', 'none')

  storage.release()
  await navigation
  await expect(loader).toBeHidden()
})

test('History uses a clear stock-in icon and curated food identity', async ({ page }) => {
  await page.route('**/api/storage', (route) => route.fulfill({ json: emptyStorage }))
  await page.route('**/api/history?limit=*', (route) => route.fulfill({
    json: {
      events: [
        {
          id: 'event-check-in-spinach',
          eventType: 'CHECK_IN',
          foodKey: 'spinach',
          quantityDelta: '200',
          displaySnapshot: {
            names: { en: 'Spinach', 'zh-CN': '菠菜' },
            quantity: '200',
            unit: 'g',
            location: 'FRIDGE',
          },
          createdAt: '2026-07-21T08:00:00Z',
          reversible: true,
        },
        {
          id: 'event-cooking-empty',
          eventType: 'COOKING',
          foodKey: 'spinach',
          quantityDelta: '0',
          displaySnapshot: {
            sessionName: 'Quick supper',
            items: [],
          },
          createdAt: '2026-07-21T08:05:00Z',
          reversible: false,
        },
      ],
    },
  }))

  await page.goto('/history')

  const entry = page.getByRole('listitem').filter({ hasText: 'Spinach' })
  await expect(entry).toBeVisible()
  await expect(entry.getByText('Added', { exact: true })).toBeVisible()
  await expect(entry.locator('[data-event-icon="stock-in"]')).toBeVisible()
  await expect(entry.locator('.food-token__icon')).toBeVisible()
  await expect(entry.locator('.food-token__monogram')).toHaveCount(0)

  const cookingEntry = page.locator('[data-event-icon="cooking-pot"]').locator('..')
  await expect(cookingEntry).toContainText('Quick supper')
  await expect(cookingEntry.locator('.history-event__meta')).toHaveCount(0)
})

test('Recipe Editor names an icon-only seasoning removal action', async ({ page }) => {
  await page.route('**/api/storage', (route) => route.fulfill({ json: emptyStorage }))
  await page.route('**/api/recipes/saved-seasoning', (route) => route.fulfill({
    json: {
      id: 'saved-seasoning',
      name: 'Simple pasta',
      description: null,
      baseYield: 2,
      multiplier: 1,
      ingredients: [
        { id: 'salt', nameKey: 'Salt', baseAmount: 'As needed' },
      ],
      instructions: [],
      originType: 'personal',
      originId: null,
      sourceUrl: null,
      sourcePublisher: null,
      lastCookedPortion: null,
      createdAt: '2026-07-21T08:00:00Z',
      updatedAt: '2026-07-21T08:00:00Z',
    },
  }))

  await page.goto('/recipes/editor?savedId=saved-seasoning')

  await expect(page.getByRole('button', { name: 'Remove Salt' })).toBeVisible()
})
