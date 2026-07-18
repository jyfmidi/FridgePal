import { test, expect } from '@playwright/test'

test('placeholder page renders the Fridgital title', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Fridgital').first()).toBeVisible()
})
