import { expect, test, type Page, type Route } from '@playwright/test'
import { signInFreshUser } from '../helpers/auth'

const emptyStorage = {
  useSoon: [],
  inventory: [],
}

const rescueStorage = {
  useSoon: [],
  inventory: [
    ['chicken-breast', 'Chicken breast'],
    ['spinach', 'Spinach'],
    ['mushrooms', 'Mushrooms'],
    ['broccoli', 'Broccoli'],
    ['tofu', 'Tofu'],
  ].map(([foodKey, name]) => ({
    foodKey,
    names: { en: name, 'zh-CN': name },
    visualKey: foodKey,
    quantity: '100',
    unit: 'g',
    location: 'FRIDGE',
    urgency: 'LATER',
  })),
}

const rescueSearchResult = {
  sessionId: 'session-new',
  recipes: [{
    title: 'Quick rescue bowl',
    description: null,
    baseYield: 2,
    ingredients: [],
    steps: ['Combine and cook.'],
    sourceUrls: [],
    analysisStatus: 'READY',
    warnings: [],
  }],
  recipeErrors: [],
}

async function initializeRescueSelection(page: Page) {
  const selectedIds = rescueStorage.inventory.map((food) => `${food.foodKey}-FRIDGE`)
  await page.addInitScript(({ ids, foods }) => {
    localStorage.setItem('fridgital.rescue.selection.v1', JSON.stringify(ids))
    localStorage.setItem('fridgital.inventory.v1', JSON.stringify(foods.map((food) => ({
      id: `${food.foodKey}-FRIDGE`,
      foodKey: food.foodKey,
      nameKey: `foods.${food.foodKey === 'chicken-breast' ? 'chickenBreast' : food.foodKey}`,
      names: food.names,
      quantity: Number(food.quantity),
      unit: food.unit,
      location: 'fridge',
      urgency: 'neutral',
    }))))
  }, { ids: selectedIds, foods: rescueStorage.inventory })
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
  await signInFreshUser(page)
  const storage = controlledStorageResponse(page)
  await storage.install()

  const navigation = page.goto('/')

  const loader = page.getByRole('status').filter({ hasText: 'Loading Fridge Pal…' })
  await expect(loader).toBeVisible()
  const character = loader.locator('.fridge-pal-loader__mark')
  await expect(character).toBeVisible()
  const mark = loader.locator('.fridge-pal-loader__mark')
  const label = loader.locator('.fridge-pal-loader__label')
  const markToLabelGap = await loader.evaluate((_, elements) => {
    const markBounds = elements.mark.getBoundingClientRect()
    const labelBounds = elements.label.getBoundingClientRect()
    return labelBounds.top - markBounds.bottom
  }, { mark: await mark.elementHandle(), label: await label.elementHandle() })
  expect(markToLabelGap).toBeGreaterThanOrEqual(0)
  expect(markToLabelGap).toBeLessThanOrEqual(32)

  storage.release()
  await navigation
  await expect(loader).toBeHidden()
  await expect.poll(() => storage.requestCount).toBe(1)
})

test('reduced motion keeps the hydration status without animating the character', async ({ page }) => {
  await signInFreshUser(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  const storage = controlledStorageResponse(page)
  await storage.install()

  const navigation = page.goto('/')

  const loader = page.getByRole('status').filter({ hasText: 'Loading Fridge Pal…' })
  await expect(loader).toBeVisible()
  const character = loader.locator('.fridge-pal-loader__mark')
  await expect(character).toBeVisible()
  await expect(character).toHaveCSS('animation-name', 'none')

  storage.release()
  await navigation
  await expect(loader).toBeHidden()
})

test('History uses a clear stock-in icon and curated food identity', async ({ page }) => {
  await signInFreshUser(page)
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
        ...[
          ['EDIT', 'edit'],
          ['MOVE', 'move'],
          ['MANUAL_CONSUMPTION', 'consume'],
          ['DISCARD', 'trash'],
          ['REVERSAL', 'undo'],
        ].map(([eventType, suffix], index) => ({
          id: `event-${suffix}`,
          eventType,
          foodKey: 'spinach',
          quantityDelta: eventType === 'MANUAL_CONSUMPTION' || eventType === 'DISCARD' ? '-10' : '0',
          displaySnapshot: {
            names: { en: 'Spinach', 'zh-CN': '菠菜' },
            quantity: '10',
            unit: 'g',
            location: 'FRIDGE',
            originalEventType: eventType === 'REVERSAL' ? 'CHECK_IN' : undefined,
          },
          createdAt: `2026-07-21T08:${10 + index}:00Z`,
          reversible: false,
        })),
      ],
    },
  }))

  await page.goto('/history')

  const entry = page.locator('[data-event-icon="stock-in"]').locator('..')
  await expect(entry).toBeVisible()
  await expect(entry.getByText('Added', { exact: true })).toBeVisible()
  await expect(entry.locator('[data-event-icon="stock-in"]')).toBeVisible()
  await expect(entry.locator('.food-token__icon')).toBeVisible()
  await expect(entry.locator('.food-token__monogram')).toHaveCount(0)

  const cookingEntry = page.locator('[data-event-icon="cooking-pot"]').locator('..')
  await expect(cookingEntry).toContainText('Quick supper')
  await expect(cookingEntry.locator('.history-event__meta')).toHaveCount(0)
  for (const icon of ['stock-in', 'edit', 'move', 'consume', 'cooking-pot', 'trash', 'undo']) {
    await expect(page.locator(`[data-event-icon="${icon}"]`)).toHaveCount(1)
  }
})

test('History prefers Simplified Chinese snapshot names for foods and cooking items', async ({ page }) => {
  await signInFreshUser(page)
  await page.route('**/api/storage', (route) => route.fulfill({ json: emptyStorage }))
  await page.route('**/api/history?limit=*', (route) => route.fulfill({
    json: {
      events: [
        {
          id: 'event-check-in-spinach-zh',
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
          reversible: false,
        },
        {
          id: 'event-cooking-tomatoes-zh',
          eventType: 'COOKING',
          foodKey: 'tomatoes',
          quantityDelta: '-100',
          displaySnapshot: {
            sessionName: '晚餐',
            items: [{ foodKey: 'tomatoes', names: { en: 'Tomatoes', 'zh-CN': '番茄' } }],
          },
          createdAt: '2026-07-21T08:05:00Z',
          reversible: false,
        },
      ],
    },
  }))

  await page.goto('/')
  await page.locator('.user-widget__locale').evaluate((button: HTMLButtonElement) => button.click())
  await page.getByRole('link', { name: '记录' }).click()

  const addedEntry = page.getByRole('listitem').filter({ hasText: '菠菜' })
  await expect(addedEntry).toBeVisible()
  await expect(addedEntry).not.toContainText('Spinach')
  await expect(page.getByRole('img', { name: '番茄' })).toBeVisible()
})

test('Recipe Editor names an icon-only seasoning removal action', async ({ page }) => {
  await signInFreshUser(page)
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

test('new meal idea indicator belongs only to the History destination', async ({ page }) => {
  await signInFreshUser(page)
  await initializeRescueSelection(page)
  await page.route('**/api/storage', (route) => route.fulfill({ json: rescueStorage }))
  await page.route('**/api/rescue/search', (route) => route.fulfill({ json: rescueSearchResult }))

  await page.goto('/rescue')
  await page.getByRole('button', { name: 'Find meal ideas' }).click()

  const indicators = page.locator('.app-nav__red-dot')
  await expect(indicators).toHaveCount(1)
  const historyLink = page.getByRole('link', { name: 'History New meal idea available' })
  await expect(historyLink).toHaveAttribute('href', '/history')
  await expect(historyLink.locator('.app-nav__red-dot')).toHaveCount(1)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await expect(indicators.first()).toHaveCSS('animation-name', 'none')
})

test('quick Rescue search does not flash the compact loader', async ({ page }) => {
  await signInFreshUser(page)
  await initializeRescueSelection(page)
  await page.route('**/api/storage', (route) => route.fulfill({ json: rescueStorage }))
  let releaseSearch!: () => void
  const searchReleased = new Promise<void>((resolve) => {
    releaseSearch = resolve
  })
  await page.route('**/api/rescue/search', async (route) => {
    await searchReleased
    await route.fulfill({ json: rescueSearchResult })
  })

  await page.goto('/rescue')
  const searchRequest = page.waitForRequest('**/api/rescue/search')
  await page.getByRole('button', { name: 'Find meal ideas' }).click()
  await searchRequest
  await page.waitForTimeout(75)

  await expect(page.getByRole('status').filter({ hasText: 'Searching for recipe ideas…' })).toBeHidden()
  releaseSearch()
  await expect(page).toHaveURL('/rescue/results')
})

test('slow Rescue search reveals then hides the reduced-motion compact loader', async ({ page }) => {
  await signInFreshUser(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await initializeRescueSelection(page)
  await page.route('**/api/storage', (route) => route.fulfill({ json: rescueStorage }))
  let releaseSearch!: () => void
  const searchReleased = new Promise<void>((resolve) => {
    releaseSearch = resolve
  })
  await page.route('**/api/rescue/search', async (route) => {
    await searchReleased
    await route.fulfill({ json: rescueSearchResult })
  })

  await page.goto('/rescue')
  await page.getByRole('button', { name: 'Find meal ideas' }).click()

  const loader = page.getByRole('status').filter({ hasText: 'Searching for recipe ideas…' })
  await expect(loader).toBeVisible()
  const character = loader.locator('.fridge-pal-loader__mark')
  await expect(character).toBeVisible()
  await expect(character).toHaveCSS('animation-name', 'none')

  releaseSearch()
  await expect(loader).toBeHidden()
})
