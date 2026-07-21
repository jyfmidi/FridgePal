/* Phase P3 visual verification capture for the brand-polish pass.
 * Run with dev server on :5173 and backend on :8000:
 *   node e2e/phase-p3-capture.mjs
 * Screenshots land in e2e/shots/.
 */
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const BASE = 'http://localhost:5173'
const SHOTS = new URL('./shots/', import.meta.url).pathname
mkdirSync(SHOTS, { recursive: true })

const MOBILE = { width: 390, height: 844 }
const DESKTOP = { width: 1280, height: 800 }
const LANDSCAPE = { width: 844, height: 390 }

const browser = await chromium.launch()

async function shot(page, name) {
  await page.screenshot({ path: `${SHOTS}${name}.png` })
  console.log(`captured ${name}.png`)
}

async function captureAuth() {
  const page = await browser.newPage({ viewport: MOBILE })
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(900) // let the mascot entrance settle
  await shot(page, 'mobile-login')

  await page.goto(`${BASE}/register`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(900)
  await shot(page, 'mobile-register')
  await page.close()

  const desk = await browser.newPage({ viewport: DESKTOP })
  await desk.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await desk.waitForTimeout(900)
  await shot(desk, 'desktop-login')
  await desk.goto(`${BASE}/register`, { waitUntil: 'networkidle' })
  await desk.waitForTimeout(900)
  await shot(desk, 'desktop-register')
  await desk.close()

  const land = await browser.newPage({ viewport: LANDSCAPE })
  await land.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await land.waitForTimeout(900)
  await shot(land, 'landscape-login')
  // reduced-motion check: mascot entrance animation must be disabled
  await land.emulateMedia({ reducedMotion: 'reduce' })
  await land.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await land.waitForTimeout(200)
  const animState = await land.evaluate(() => {
    const el = document.querySelector('.auth-mascot, .auth-layout__mascot, [class*="mascot"]')
    if (!el) return { found: false }
    const cs = getComputedStyle(el)
    return { found: true, animation: cs.animationName, duration: cs.animationDuration, transform: cs.transform }
  })
  console.log('reduced-motion mascot:', JSON.stringify(animState))
  await shot(land, 'landscape-login-reduced-motion')
  await land.close()

  // zh-CN auth screen via the footer locale toggle
  const zh = await browser.newPage({ viewport: MOBILE })
  await zh.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await zh.locator('.auth-locale-toggle').click()
  await zh.waitForTimeout(500)
  console.log('html lang after toggle:', await zh.evaluate(() => document.documentElement.lang))
  await shot(zh, 'mobile-login-zh')
  await zh.close()
}

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('#login-username', 'demo')
  await page.fill('#login-password', process.env.DEMO_PW)
  await page.getByRole('button', { name: /log in|登录/i }).click()
  await page.waitForURL(`${BASE}/`, { timeout: 15000 })
  await page.waitForLoadState('networkidle')
}

async function captureMain() {
  const routes = [
    ['/', 'storage'],
    ['/rescue', 'rescue'],
    ['/recipes', 'recipes'],
    ['/history', 'history'],
  ]
  for (const [viewport, tag] of [[MOBILE, 'mobile'], [DESKTOP, 'desktop']]) {
    const page = await browser.newPage({ viewport })
    await login(page)
    for (const [route, name] of routes) {
      await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle' })
      await page.waitForTimeout(500)
      await shot(page, `${tag}-${name}`)
    }
    // zh-CN on storage via the user-widget locale switcher
    if (tag === 'mobile') {
      await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
      const switcher = page.locator('[class*="locale"], [aria-label*="locale" i], [aria-label*="语言"], [aria-label*="language" i]').last()
      if (await switcher.count()) {
        await switcher.click()
        await page.waitForTimeout(500)
      } else {
        console.log('WARN: no locale switcher found on main screen')
      }
      console.log('main html lang after switch:', await page.evaluate(() => document.documentElement.lang))
      await shot(page, 'mobile-storage-zh')
    }
    await page.close()
  }
}

try {
  await captureAuth()
  await captureMain()
} finally {
  await browser.close()
}
console.log('done')
