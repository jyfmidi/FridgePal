import { expect, test } from '@playwright/test'

const PASSWORD = 'password123'

async function fillRegisterForm(page: import('@playwright/test').Page, username: string) {
  await page.getByLabel('Username', { exact: true }).fill(username)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByLabel('Confirm password', { exact: true }).fill(PASSWORD)
}

test('register a new account, reach storage, and log out', async ({ page }) => {
  const username = `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  await page.goto('/register')
  await fillRegisterForm(page, username)
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('heading', { name: 'Use soon' })).toBeVisible()
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL('/login')
})

test('authenticated users are redirected away from auth screens', async ({ page }) => {
  const username = `redir_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  await page.goto('/register')
  await fillRegisterForm(page, username)
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page).toHaveURL('/')
  await page.goto('/login')
  await expect(page).toHaveURL('/')
})

test('login rejects a wrong password with a localized message', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Username', { exact: true }).fill('demo')
  await page.getByLabel('Password', { exact: true }).fill('wrong-password-1')
  await page.getByRole('button', { name: 'Log in' }).click()
  await expect(page.getByRole('alert')).toContainText('Incorrect username or password')
})

test('duplicate registration shows a localized error', async ({ page }) => {
  const username = `dup_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  await page.goto('/register')
  await fillRegisterForm(page, username)
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page).toHaveURL('/')
  await page.getByRole('button', { name: 'Logout' }).click()
  await expect(page).toHaveURL('/login')

  await page.goto('/register')
  await fillRegisterForm(page, username)
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page.getByRole('alert')).toContainText('That username is already taken.')
})

test('client-side validation blocks an invalid username and short password', async ({ page }) => {
  await page.goto('/register')
  await page.getByLabel('Username', { exact: true }).fill('bad name!')
  await page.getByLabel('Password', { exact: true }).fill('short')
  await page.getByLabel('Confirm password', { exact: true }).fill('short')
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page.getByRole('alert')).toContainText(
    'Use 3-32 letters, numbers, underscores, or hyphens.',
  )

  await page.getByLabel('Username', { exact: true }).fill('gooduser')
  await page.getByRole('button', { name: 'Register' }).click()
  await expect(page.getByRole('alert')).toContainText('Password must be at least 8 characters.')
})
