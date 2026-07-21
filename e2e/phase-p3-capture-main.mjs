/* Phase P3 capture — authenticated main screens only. */
import { chromium } from '@playwright/test'

const BASE = 'http://localhost:5173'
const SHOTS = new URL('./shots/', import.meta.url).pathname
const MOBILE = { width: 390, height: 844 }
const DESKTOP = { width: 1280, height: 800 }

const browser = await chromium.launch()

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('#login-username', 'demo')
  await page.fill('#login-password', process.env.DEMO_PW)
  await page.getByRole('button', { name: /log in|登录/i }).click()
  await page.waitForURL(`${BASE}/`, { timeout: 15000 })
  await page.waitForLoadState('networkidle')
  console.log('after login url:', page.url(), 'cookies:', (await page.context().cookies()).map((c) => c.name).join(','))
}

const routes = [['/', 'storage'], ['/rescue', 'rescue'], ['/recipes', 'recipes'], ['/history', 'history']]

for (const [viewport, tag] of [[MOBILE, 'mobile'], [DESKTOP, 'desktop']]) {
  const page = await browser.newPage({ viewport })
  page.on('response', (r) => { if (r.url().includes('/api/')) console.log('HTTP', r.status(), r.url().replace(BASE, '')) })
  await login(page)
  for (const [route, name] of routes) {
    await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    console.log(tag, route, '->', page.url())
    await page.screenshot({ path: `${SHOTS}${tag}-${name}.png` })
  }
  if (tag === 'mobile') {
    await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
    const switcher = page.locator('button.user-widget__locale:visible').first()
    console.log('switcher count:', await switcher.count())
    if (await switcher.count()) {
      await switcher.click()
      await page.waitForTimeout(600)
    }
    console.log('main html lang after switch:', await page.evaluate(() => document.documentElement.lang))
    await page.screenshot({ path: `${SHOTS}mobile-storage-zh.png` })
  }
  await page.close()
}
await browser.close()
console.log('done')
