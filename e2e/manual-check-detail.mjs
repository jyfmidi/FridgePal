/* Manual verification for the ingredient detail/edit flow (UI-03).
 *
 * Run with the dev server on :5173 and the backend on :8000:
 *   node e2e/manual-check-detail.mjs
 *
 * Flow: open the Spinach detail view from a Storage tile, assert the aggregate
 * and lots render, reduce stock (preview + confirm), edit the lot quantity,
 * go back and assert the tile reflects the new aggregate, then switch to
 * zh-CN and confirm the view renders Chinese. Cleanup restores the original
 * lot quantity via the API so the demo data stays sane.
 */
import { chromium } from '@playwright/test'

const BASE = 'http://localhost:5173'
const API = 'http://localhost:8000'

let failures = 0
function check(condition, message) {
  if (condition) {
    console.log(`ok - ${message}`)
  } else {
    failures += 1
    console.error(`FAIL - ${message}`)
  }
}

function parseQuantity(text) {
  const match = text.replace(/,/g, '').match(/[\d.]+/)
  return match ? Number(match[0]) : Number.NaN
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 390, height: 844 } })

let originalAggregate = null

try {
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })

  const tile = page.locator('button[aria-label^="Spinach"]').first()
  await tile.waitFor()
  originalAggregate = parseQuantity(await tile.locator('.storage-tile__quantity').textContent())
  check(Number.isFinite(originalAggregate), `read original Spinach aggregate from tile (${originalAggregate})`)

  await tile.click()
  await page.waitForURL(/\/storage\/item\?.*food=spinach/)

  const hero = page.locator('.hero-card__quantity')
  await hero.waitFor()
  check(parseQuantity(await hero.textContent()) === originalAggregate, 'detail hero shows the aggregate quantity')

  const lotRows = page.locator('.lot-row')
  check((await lotRows.count()) >= 1, 'lots section shows at least one lot')

  // --- Reduce stock by 50 with preview + confirm ---
  await page.getByRole('button', { name: 'Reduce stock' }).click()
  await page.locator('.edit-section input[type="number"]').fill('50')
  const preview = await page.locator('.reduce-preview').textContent()
  check(preview.includes(String(originalAggregate - 50)), `preview shows new total (${preview.trim()})`)
  await page.getByRole('button', { name: 'Confirm reduction' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(parseQuantity(await hero.textContent()) === originalAggregate - 50, 'aggregate decreased after confirm')
  // Let the transient notice clear so the next waitFor catches a fresh one.
  await page.locator('.notice').waitFor({ state: 'hidden' })

  // --- Edit the selected lot's quantity back up by 100 ---
  await page.getByRole('button', { name: 'Edit', exact: true }).click()
  const editInput = page.locator('.edit-section input[type="number"]').first()
  await editInput.fill(String(originalAggregate + 50))
  await page.getByRole('button', { name: 'Save changes' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(parseQuantity(await hero.textContent()) === originalAggregate + 50, 'aggregate reflects the lot edit')

  // --- Back to Storage: tile shows the updated quantity ---
  await page.getByRole('button', { name: 'Back' }).click()
  await page.waitForURL(`${BASE}/`)
  const updatedTile = page.locator('button[aria-label^="Spinach"]').first()
  await updatedTile.waitFor()
  const tileQuantity = parseQuantity(await updatedTile.locator('.storage-tile__quantity').textContent())
  check(tileQuantity === originalAggregate + 50, `Storage tile shows updated quantity (${tileQuantity})`)

  // --- zh-CN rendering ---
  await page.setViewportSize({ width: 900, height: 844 })
  await page.getByRole('button', { name: '中文' }).click()
  await page.locator('button[aria-label^="菠菜"]').first().click()
  await page.waitForURL(/\/storage\/item\?.*food=spinach/)
  check((await page.locator('.hero-card__quantity').textContent()).includes('克'), 'zh-CN hero shows localized unit')
  check(await page.getByRole('button', { name: '减少库存' }).isVisible(), 'zh-CN reduce action renders')
  check((await page.locator('.card h2').first().textContent()).includes('批次'), 'zh-CN lots heading renders')
  await page.getByRole('button', { name: '返回' }).click()
  await page.waitForURL(`${BASE}/`)
  await page.getByRole('button', { name: 'EN' }).click()
} catch (error) {
  failures += 1
  console.error(`FAIL - unexpected error: ${error.message}`)
} finally {
  // Cleanup: restore the lot to its original quantity so demo data stays sane.
  if (originalAggregate !== null) {
    try {
      const lotsResponse = await fetch(`${API}/api/inventory/lots?foodKey=spinach&location=FRIDGE`)
      const { lots } = await lotsResponse.json()
      const active = lots.find((lot) => lot.status === 'ACTIVE')
      if (active) {
        const patchResponse = await fetch(`${API}/api/lots/${active.lotId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idempotencyKey: crypto.randomUUID(), quantity: String(originalAggregate) }),
        })
        check(patchResponse.ok, `cleanup restored Spinach lot to ${originalAggregate}`)
      }
    } catch (error) {
      failures += 1
      console.error(`FAIL - cleanup failed: ${error.message}`)
    }
  }
  await browser.close()
}

if (failures > 0) {
  console.error(`\n${failures} check(s) failed`)
  process.exit(1)
}
console.log('\nAll checks passed')
