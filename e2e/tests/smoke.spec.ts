import { expect, test } from '@playwright/test'
import { signInFreshUser } from '../helpers/auth'

test('Fridge Pal title and standalone brand mark render', async ({ page }) => {
  await signInFreshUser(page)
  await page.goto('/')
  await expect(page).toHaveTitle('Fridge Pal')
  await expect(page.getByRole('img', { name: 'Fridge Pal' })).toBeVisible()
})
