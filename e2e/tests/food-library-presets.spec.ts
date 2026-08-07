import { expect, test } from '@playwright/test'
import { signInFreshUser } from '../helpers/auth'

test('Add Food applies the first server Food Library preset as its defaults', async ({ page }) => {
  await signInFreshUser(page)
  await page.goto('/add-food')

  await page.getByPlaceholder('Search the Food Library').fill('Bok choy')
  const bokChoy = page.getByRole('button', { name: 'Bok choy', exact: true })
  await expect(bokChoy).toBeVisible()
  await expect(bokChoy.locator('svg.food-token__icon')).toBeVisible()
  await expect(bokChoy.locator('.food-token__monogram')).toHaveCount(0)

  await bokChoy.click()

  await expect(page.getByLabel('Quantity')).toHaveValue('300')
  await expect(page.getByLabel('Unit')).toHaveValue('g')
  const locations = page.getByRole('group', { name: 'Storage location' })
  await expect(locations.getByRole('button', { name: 'Fridge' })).toHaveAttribute('aria-pressed', 'true')

  const expectedExpiry = await page.evaluate(() => {
    const date = new Date(`${new Date().toISOString().slice(0, 10)}T00:00:00`)
    date.setDate(date.getDate() + 3)
    const offset = date.getTimezoneOffset()
    return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10)
  })
  await expect(page.getByLabel('Use-by date')).toHaveValue(expectedExpiry)
})
