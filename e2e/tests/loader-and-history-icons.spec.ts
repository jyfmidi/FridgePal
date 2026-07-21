import { expect, test, type Page, type Route } from '@playwright/test'

const emptyStorage = {
  useSoon: [],
  inventory: [],
}

function controlledStorageResponse(page: Page) {
  let releaseResponse!: () => void
  const responseReleased = new Promise<void>((resolve) => {
    releaseResponse = resolve
  })

  return {
    release: releaseResponse,
    install: () => page.route('**/api/storage', async (route: Route) => {
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
  await expect(loader.locator('[data-motion="wiggle-hop"]')).toBeVisible()

  storage.release()
  await navigation
  await expect(loader).toBeHidden()
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
})
