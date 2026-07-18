/* One-off visual verification screenshots for the warm-refinement redesign. */
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const OUT = new URL('./shots/', import.meta.url).pathname
mkdirSync(OUT, { recursive: true })

const pages = ['/', '/rescue', '/rescue/choose', '/rescue/results', '/recipes', '/add-food', '/history']
const viewports = [
  { name: 'mobile', width: 390, height: 844 },
  { name: 'desktop', width: 1280, height: 800 },
]

const browser = await chromium.launch()
for (const vp of viewports) {
  const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } })
  for (const path of pages) {
    await page.goto(`http://localhost:5173${path}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(450) // let entrance animations settle
    const name = path === '/' ? 'storage' : path.replaceAll('/', '-').slice(1)
    await page.screenshot({ path: `${OUT}${vp.name}-${name}.png`, fullPage: false })
  }
  await page.close()
}
await browser.close()
console.log('done ->', OUT)
