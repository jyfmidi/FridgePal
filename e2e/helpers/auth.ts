import { expect, request, type Page } from '@playwright/test'

/**
 * Registers a fresh account through the API and injects the session cookie
 * into the browser context.
 *
 * E2E flows that do not test auth still must pass the router guard, so they
 * need a valid session. Going through the API keeps this fast, unique per run,
 * and independent of the demo account password.
 */
export async function signInFreshUser(page: Page): Promise<void> {
  const username = `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  const api = await request.newContext({ baseURL: 'http://localhost:5173' })
  try {
    let res = await api.post('/api/auth/register', {
      data: { username, password: 'password123' },
    })
    // Registration is rate-limited per client address
    // (AUTH_REGISTER_RATE_PER_MINUTE) and the whole suite shares one address,
    // so bursts occasionally hit 429; let the sliding window drain and retry.
    for (let attempt = 0; attempt < 5 && res.status() === 429; attempt++) {
      await new Promise((resolve) => setTimeout(resolve, 12_000))
      res = await api.post('/api/auth/register', {
        data: { username, password: 'password123' },
      })
    }
    expect(res.status(), `register failed: ${await res.text()}`).toBe(201)
    const setCookie = res.headersArray().find((h) => h.name.toLowerCase() === 'set-cookie')
    const cookiePair = setCookie?.value?.split(';')[0]
    expect(cookiePair).toBeTruthy()
    await page.context().addCookies([
      {
        name: 'fp_session',
        value: cookiePair!.split('=').slice(1).join('='),
        url: 'http://localhost:5173',
      },
    ])
  } finally {
    await api.dispose()
  }
}
