import { test, expect } from '@playwright/test'

test('Fridge Pal title and standalone brand mark render', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle('Fridge Pal')
  await expect(page.getByRole('img', { name: 'Fridge Pal' })).toBeVisible()
})
