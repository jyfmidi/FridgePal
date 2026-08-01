/**
 * Style-consistency audit: measures key recurring surfaces (cards, empty
 * states, page headings) across routes and reports divergences.
 *
 * Usage: node scripts/style-audit.mjs
 */
import { chromium } from 'playwright'

const BASE = 'http://localhost:5173'
const ROUTES = ['/', '/rescue', '/recipes', '/history', '/add-food', '/recipes/editor']

const browser = await chromium.launch()
const context = await browser.newContext({ baseURL: BASE })
const login = await context.request.post(`${BASE}/api/auth/login`, {
  data: { username: 'demo', password: process.env.FRIDGE_PAL_DEMO_PASSWORD || 'demo12345' },
})
const setCookie = (await login.headersArray().find((h) => h.name.toLowerCase() === 'set-cookie'))
  ?.value?.split(';')[0]
await context.addCookies([{ name: 'fp_session', value: setCookie.split('=').slice(1).join('='), url: BASE }])

const page = await context.newPage()
await page.setViewportSize({ width: 390, height: 844 })

// Sample: for every element matching card-ish heuristics, record surface props.
const samples = []
for (const route of ROUTES) {
  await page.goto(route, { waitUntil: 'networkidle' }).catch(() => {})
  await page.waitForTimeout(750)
  const data = await page.evaluate(() => {
    const out = []
    const cardLike = document.querySelectorAll(
      '[class*="card"], [class*="event"], [class*="empty"], [class*="swatch"], [class*="cell"], [class*="tile"]',
    )
    for (const el of cardLike) {
      const s = getComputedStyle(el)
      const r = el.getBoundingClientRect()
      if (r.width < 40 || r.height < 24) continue
      const cls = (el.className || '').toString().split(/\s+/).filter(Boolean).join('.')
      out.push({
        cls: cls.slice(0, 60),
        bg: s.backgroundColor,
        radius: s.borderRadius,
        shadow: s.boxShadow === 'none' ? 'none' : 'shadow',
        pad: `${s.paddingTop} ${s.paddingRight} ${s.paddingBottom} ${s.paddingLeft}`,
        fs: s.fontSize,
      })
    }
    return out
  })
  for (const d of data) samples.push({ route, ...d })
}

// Value distributions for card-like surfaces (rounded to 1px).
const bucket = (v) => v.replace(/(\d+\.\d)/g, (m) => Number(m).toFixed(0)).replace(/px/g, 'px')
const radiusDist = new Map()
const padDist = new Map()
const bgDist = new Map()
for (const s of samples) {
  for (const [dist, v] of [[radiusDist, s.radius], [padDist, s.pad], [bgDist, s.bg]]) {
    const key = bucket(v)
    const entry = dist.get(key) ?? { count: 0, routes: new Set(), cls: new Set() }
    entry.count += 1
    entry.routes.add(s.route)
    entry.cls.add(s.cls)
    dist.set(key, entry)
  }
}
console.log('=== Border-radius distribution (card-like surfaces) ===')
for (const [v, e] of [...radiusDist].sort((a, b) => b[1].count - a[1].count)) {
  console.log(`  ${v.padEnd(24)} x${e.count}  routes=[${[...e.routes].join(', ')}]  cls=[${[...e.cls].slice(0, 4).join(', ')}]`)
}
console.log('\n=== Padding distribution ===')
for (const [v, e] of [...padDist].sort((a, b) => b[1].count - a[1].count)) {
  console.log(`  [${v}] x${e.count}  cls=[${[...e.cls].slice(0, 3).join(', ')}]`)
}
console.log('\n=== Background distribution ===')
for (const [v, e] of [...bgDist].sort((a, b) => b[1].count - a[1].count)) {
  console.log(`  ${v.padEnd(24)} x${e.count}  cls=[${[...e.cls].slice(0, 3).join(', ')}]`)
}

await browser.close()
