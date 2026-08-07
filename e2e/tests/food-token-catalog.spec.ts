import { expect, test } from '@playwright/test'
import { signInFreshUser } from '../helpers/auth'

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
