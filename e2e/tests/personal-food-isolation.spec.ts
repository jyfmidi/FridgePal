import { expect, test, type Page } from '@playwright/test'

const PASSWORD = 'password123'

function uniqueName(): string {
  return `Private pantry ${Date.now()} ${Math.random().toString(36).slice(2, 8)}`
}

async function register(page: Page, username: string): Promise<void> {
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  await page.getByLabel('Username', { exact: true }).fill(username)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByLabel('Confirm password', { exact: true }).fill(PASSWORD)
  const registerButton = page.getByRole('button', { name: 'Register' })
  await expect(registerButton).toBeEnabled()
  const response = page.waitForResponse((candidate) => (
    candidate.url().endsWith('/api/auth/register')
    && candidate.request().method() === 'POST'
  ))
  await registerButton.click()
  await expect((await response).status()).toBe(201)
  await expect(page).toHaveURL('/')
}

async function openAddFood(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Add food' }).click()
  await expect(page.getByPlaceholder('Search the Food Library')).toBeVisible()
}

async function createCustomFood(page: Page, name: string): Promise<void> {
  await openAddFood(page)
  await page.getByPlaceholder('Search the Food Library').fill(name)
  await saveCustomFood(page, name)
}

async function saveCustomFood(page: Page, name: string): Promise<void> {
  await page.getByRole('button', { name: `Create "${name}"` }).click()
  await page.getByRole('button', { name: 'Save food' }).click()
  await expect(page).toHaveURL('/')
}

test('personal food suggestions are isolated after switching accounts', async ({ page }) => {
  const suffix = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  const alice = `alice_${suffix}`
  const bob = `bob_${suffix}`
  const foodName = uniqueName()

  await page.goto('/register')
  await register(page, alice)
  await createCustomFood(page, foodName)

  await openAddFood(page)
  const search = page.getByPlaceholder('Search the Food Library')
  await search.fill(foodName)
  await expect(page.getByRole('button', { name: foodName, exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: `Create "${foodName}"` })).toHaveCount(0)

  await page.getByRole('button', { name: 'Back' }).click()
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL('/login')

  await page.getByRole('link', { name: 'Register' }).click()
  await expect(page).toHaveURL('/register')
  await register(page, bob)
  await openAddFood(page)
  await search.fill(foodName)
  await expect(page.getByRole('button', { name: foodName, exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: `Create "${foodName}"` })).toBeVisible()

  await saveCustomFood(page, foodName)
  await openAddFood(page)
  await search.fill(foodName)
  await expect(page.getByRole('button', { name: foodName, exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: `Create "${foodName}"` })).toHaveCount(0)
})
