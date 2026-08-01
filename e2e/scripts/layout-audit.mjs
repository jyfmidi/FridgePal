/**
 * Layout audit: renders every main route at mobile + desktop widths and
 * reports horizontal overflow and text-overflow issues.
 *
 * Usage: node scripts/layout-audit.mjs [--shot]
 * Requires the backend on :8000 and the Vite dev server on :5173.
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const BASE = 'http://localhost:5173'
const SHOTS = process.argv.includes('--shot')
const OUT = 'shots/layout-audit'
mkdirSync(OUT, { recursive: true })

const VIEWPORTS = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'desktop', width: 1440, height: 900 },
]

// Route -> optional setup to run before auditing it.
const ROUTES = [
  ['/', 'storage'],
  ['/rescue', 'rescue'],
  ['/rescue/choose', 'rescue-choose'],
  ['/recipes', 'recipes'],
  ['/recipes/editor', 'recipe-editor'],
  ['/history', 'history'],
  ['/add-food', 'add-food'],
  ['/storage/item?foodKey=spinach', 'storage-item'],
  ['/dev/tokens', 'dev-tokens'],
  ['/login', 'login'],
  ['/register', 'register'],
]

const browser = await chromium.launch()
const context = await browser.newContext({ baseURL: BASE })

// Sign in as the demo account via the API and inject the cookie.
const login = await context.request.post(`${BASE}/api/auth/login`, {
  data: { username: 'demo', password: process.env.FRIDGE_PAL_DEMO_PASSWORD || 'demo12345' },
})
if (login.status() !== 200) {
  console.error('demo login failed:', login.status(), await login.text())
  process.exit(1)
}
const setCookie = (await login.headersArray().find((h) => h.name.toLowerCase() === 'set-cookie'))
  ?.value?.split(';')[0]
await context.addCookies([
  { name: 'fp_session', value: setCookie.split('=').slice(1).join('='), url: BASE },
])

// Seed a rescue selection + results session through localStorage so the
// choose/results routes render with content.
await context.addInitScript(() => {
  const foods = ['spinach', 'yogurt', 'chicken-breast', 'mushrooms', 'broccoli'].map(
    (key) => `${key}-FRIDGE`,
  )
  localStorage.setItem('fridgital.rescue.selection.v1', JSON.stringify(foods))
})

const LOCALE_RUNS = ['en', 'zh-CN']
const failures = []
// Produce a real fixture rescue session once so results render with content.
{
  const seedPage = await context.newPage()
  await seedPage.setViewportSize({ width: 390, height: 844 })
  await seedPage.goto('/rescue', { waitUntil: 'networkidle' })
  await seedPage.getByRole('button', { name: 'Find meal ideas' }).click()
  await seedPage.waitForURL('**/rescue/results', { timeout: 15000 }).catch(() => {})
  await seedPage.close()
}

for (const locale of LOCALE_RUNS) {
  if (locale !== 'en') {
    await context.addInitScript(() => localStorage.setItem('fridge-pal-locale', 'zh-CN'))
  }
  for (const viewport of VIEWPORTS) {
  const page = await context.newPage()
  await page.setViewportSize({ width: viewport.width, height: viewport.height })

  for (const [route, name] of ROUTES) {
    await page.goto(route, { waitUntil: 'networkidle' }).catch(() => {})
    if (route === '/rescue') {
      // Continue into results through the real UI so the session renders.
      await page.getByRole('button', { name: 'Find meal ideas' }).click().catch(() => {})
      await page.waitForURL('**/rescue/results', { timeout: 15000 }).catch(() => {})
    }
    await page.waitForTimeout(750)

    const report = await page.evaluate(() => {
      const vw = window.innerWidth
      const issues = []
      const doc = document.documentElement
      if (doc.scrollWidth > vw + 1) {
        issues.push(`PAGE-OVERFLOW scrollWidth=${doc.scrollWidth} vw=${vw}`)
      }

      const seen = new Set()
      for (const el of document.querySelectorAll('body *')) {
        if (seen.has(el)) continue
        seen.add(el)
        const style = getComputedStyle(el)
        if (style.display === 'none' || style.visibility === 'hidden') continue
        const r = el.getBoundingClientRect()
        if (r.width === 0 && r.height === 0) continue
        if (style.position === 'fixed' || style.position === 'sticky') continue
        // Skip SVG internals (icons are intentionally self-contained).
        if (el.closest('svg')) continue

        // Text content overflowing its own box (unwrapped long words etc.).
        if (
          el.scrollWidth > el.clientWidth + 1 &&
          el.clientWidth > 0 &&
          style.overflowX === 'visible' &&
          el.textContent?.trim()
        ) {
          issues.push(
            `TEXT-OVERFLOW <${el.tagName.toLowerCase()} class="${(el.className || '').toString().slice(0, 60)}"> "${el.textContent.trim().slice(0, 50)}" (${el.clientWidth}/${el.scrollWidth}px)`,
          )
        }

        // Element sticking out past the right edge.
        if (r.right > vw + 1) {
          issues.push(
            `ELEMENT-PAST-EDGE <${el.tagName.toLowerCase()} class="${(el.className || '').toString().slice(0, 60)}"> right=${Math.round(r.right)} vw=${vw} "${el.textContent?.trim().slice(0, 40)}"`,
          )
        }
      }
      return issues
    })

    if (SHOTS) {
      await page.screenshot({ path: `${OUT}/${viewport.name}-${name}.png`, fullPage: false })
    }
    if (report.length) {
      failures.push({ viewport: viewport.name, locale, route, name, report })
    } else {
      console.log(`OK  ${locale.padEnd(6)} ${viewport.name.padEnd(8)} ${route}`)
    }
    await page.goto('about:blank').catch(() => {})
  }
  await page.close()
  }
}

// Long-username check: the user widget must not overflow at the max length.
{
  const longName = 'x'.repeat(32)
  const reg = await context.request.post(`${BASE}/api/auth/register`, {
    data: { username: longName, password: 'password123' },
  })
  if (reg.status() === 201) {
    const cookie = (await reg.headersArray().find((h) => h.name.toLowerCase() === 'set-cookie'))
      ?.value?.split(';')[0]
    const longContext = await browser.newContext({ baseURL: BASE })
    await longContext.addCookies([
      { name: 'fp_session', value: cookie.split('=').slice(1).join('='), url: BASE },
    ])
    for (const viewport of VIEWPORTS) {
      const page = await longContext.newPage()
      await page.setViewportSize({ width: viewport.width, height: viewport.height })
      await page.goto('/', { waitUntil: 'networkidle' })
      await page.waitForTimeout(750)
      const report = await page.evaluate(() => {
        const vw = window.innerWidth
        const out = []
        if (document.documentElement.scrollWidth > vw + 1) {
          out.push(`PAGE-OVERFLOW scrollWidth=${document.documentElement.scrollWidth} vw=${vw}`)
        }
        for (const el of document.querySelectorAll('.user-widget *')) {
          const r = el.getBoundingClientRect()
          if (r.right > vw + 1 || r.left < -1) {
            out.push(`USER-WIDGET <${el.tagName.toLowerCase()} class="${(el.className || '').toString().slice(0, 50)}"> left=${Math.round(r.left)} right=${Math.round(r.right)} vw=${vw}`)
          }
        }
        return out
      })
      if (report.length) {
        failures.push({ viewport: viewport.name, route: '/ (32-char user)', name: 'long-user', report })
      } else {
        console.log(`OK  ${viewport.name.padEnd(8)} / (32-char user)`)
      }
      await page.close()
    }
    await longContext.close()
  } else {
    console.log('long-user register skipped:', reg.status())
  }
}

await browser.close()

if (failures.length) {
  console.log(`\n${failures.length} route/viewport combinations have issues:\n`)
  for (const f of failures) {
    console.log(`== ${f.locale ?? 'en'} ${f.viewport} ${f.route}`)
    for (const line of f.report) console.log(`   ${line}`)
  }
  process.exit(1)
}
console.log('\nNo overflow issues found.')
