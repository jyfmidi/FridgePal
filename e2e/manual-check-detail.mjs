/* Manual verification for the ingredient detail/edit flow (UI-03, redesigned).
 *
 * Run with the dev server on :5173 and the backend on :8000:
 *   node e2e/manual-check-detail.mjs
 *
 * Flow: open the Spinach detail view from a Storage tile, assert the hero,
 * step the quantity down by 50 (hint mentions oldest first), confirm via the
 * sticky Update storage bar, assert the aggregate dropped and the tile follows.
 * Then step up by 50 (earliest-lot patch), change the use-by date, open the
 * lots disclosure and exercise per-lot discard on a scratch lot, and spot-check
 * zh-CN rendering. Cleanup restores the demo data via the API.
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

async function activeSpinachLot() {
  const response = await fetch(`${API}/api/inventory/lots?foodKey=spinach&location=FRIDGE`)
  const { lots } = await response.json()
  return lots.filter((lot) => lot.status === 'ACTIVE').sort((a, b) => a.storedOn.localeCompare(b.storedOn))[0] ?? null
}

async function spinachAggregate() {
  const response = await fetch(`${API}/api/storage`)
  const { inventory } = await response.json()
  const item = inventory.find((entry) => entry.foodKey === 'spinach' && entry.location === 'FRIDGE')
  return item ? Number(item.quantity) : 0
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 390, height: 844 } })

let originalAggregate = null
let originalExpiresOn = null

try {
  originalAggregate = await spinachAggregate()
  originalExpiresOn = (await activeSpinachLot())?.expiresOn ?? null
  check(Number.isFinite(originalAggregate), `read original Spinach aggregate from API (${originalAggregate})`)

  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
  const tile = page.locator('button[aria-label^="Spinach"]').first()
  await tile.waitFor()
  await tile.click()
  await page.waitForURL(/\/storage\/item\?.*food=spinach/)

  // --- Hero ---
  const heroName = page.locator('.hero-card__name')
  await heroName.waitFor()
  check((await heroName.textContent()) === 'Spinach', 'hero shows the food name')
  check((await page.locator('.hero-card__badges').textContent()).includes('Fridge'), 'hero badges include the location')

  const quantityInput = page.locator('.quantity-input')
  check(parseQuantity(await quantityInput.inputValue()) === originalAggregate, 'quantity input starts at the aggregate')

  // --- Step down by 50 → hint → confirm ---
  await page.getByRole('button', { name: 'Decrease quantity' }).click()
  const hint = page.locator('.effect-hint')
  await hint.waitFor()
  check((await hint.textContent()).includes('oldest first'), `decrease hint mentions oldest first (${(await hint.textContent()).trim()})`)
  const confirmBar = page.locator('.confirm-bar')
  await confirmBar.waitFor()
  check((await confirmBar.textContent()).includes('→'), 'confirm bar shows the quantity summary')
  await page.getByRole('button', { name: 'Update storage' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(parseQuantity(await quantityInput.inputValue()) === originalAggregate - 50, 'aggregate decreased by 50 after confirm')
  check((await spinachAggregate()) === originalAggregate - 50, 'server aggregate decreased by 50')
  await page.locator('.notice').waitFor({ state: 'hidden' })

  // --- Step up by 50 → earliest-lot patch ---
  await page.getByRole('button', { name: 'Increase quantity' }).click()
  check((await page.locator('.effect-hint').textContent()).includes('earliest lot'), 'increase hint mentions the earliest lot')
  await page.getByRole('button', { name: 'Update storage' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(parseQuantity(await quantityInput.inputValue()) === originalAggregate, 'aggregate restored after increase')
  await page.locator('.notice').waitFor({ state: 'hidden' })

  // --- Date change persists on the earliest lot ---
  const dateInput = page.locator('input[type="date"]').first()
  const newDate = '2030-06-15'
  await dateInput.fill(newDate)
  await page.getByRole('button', { name: 'Update storage' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check((await activeSpinachLot())?.expiresOn === newDate, 'use-by date persisted on the earliest lot')
  await page.locator('.notice').waitFor({ state: 'hidden' })

  // --- Lots disclosure: opens, per-lot edit + discard work ---
  const disclosure = page.locator('.lots-disclosure')
  await disclosure.locator('summary').click()
  check(await disclosure.locator('.lot-row').first().isVisible(), 'lots disclosure opens and lists lots')

  // Discard flow on a scratch lot created via check-in so demo data is untouched.
  const checkInResponse = await fetch(`${API}/api/inventory/check-in`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      idempotencyKey: crypto.randomUUID(),
      foodKey: 'spinach',
      names: { en: 'Spinach', 'zh-CN': '菠菜' },
      quantity: '10',
      unit: 'g',
      location: 'FRIDGE',
      storedOn: '2030-01-01',
      expirySource: 'NONE',
    }),
  })
  check(checkInResponse.ok, 'scratch lot checked in for the discard test')
  await page.reload({ waitUntil: 'networkidle' })
  await disclosure.locator('summary').click()
  const scratchRow = disclosure.locator('.lot-row', { hasText: '10 g' }).first()
  await scratchRow.click()
  await page.getByRole('button', { name: 'Edit lot' }).click()
  check(await page.locator('.edit-section').isVisible(), 'per-lot edit section opens')
  await page.getByRole('button', { name: 'Done' }).click()
  await page.getByRole('button', { name: 'Discard', exact: true }).click()
  await page.getByRole('button', { name: 'Confirm discard?' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(true, 'two-step discard completed with confirmation banner')
  check((await spinachAggregate()) === originalAggregate, 'aggregate back to original after scratch discard')

  // --- Back to Storage: tile shows the restored quantity ---
  await page.getByRole('button', { name: 'Back' }).click()
  await page.waitForURL(`${BASE}/`)
  const updatedTile = page.locator('button[aria-label^="Spinach"]').first()
  await updatedTile.waitFor()
  check(parseQuantity(await updatedTile.locator('.storage-tile__quantity').textContent()) === originalAggregate, 'Storage tile shows the restored quantity')

  // --- zh-CN rendering ---
  await page.setViewportSize({ width: 900, height: 844 })
  await page.getByRole('button', { name: '中文' }).click()
  await page.locator('button[aria-label^="菠菜"]').first().click()
  await page.waitForURL(/\/storage\/item\?.*food=spinach/)
  check((await page.locator('.hero-card__name').textContent()) === '菠菜', 'zh-CN hero name renders')
  await page.getByRole('button', { name: '减少数量' }).click()
  check((await page.locator('.effect-hint').textContent()).includes('最早存入'), 'zh-CN decrease hint renders')
  check(await page.getByRole('button', { name: '更新库存' }).isVisible(), 'zh-CN update action renders')
  check((await page.locator('.lots-disclosure summary').textContent()).includes('批次'), 'zh-CN lots disclosure renders')
  await page.getByRole('button', { name: '返回' }).click()
  await page.waitForURL(`${BASE}/`)
  await page.getByRole('button', { name: 'EN' }).click()
} catch (error) {
  failures += 1
  console.error(`FAIL - unexpected error: ${error.message}`)
} finally {
  // Cleanup: restore the earliest Spinach lot's quantity and use-by date.
  if (originalAggregate !== null) {
    try {
      const active = await activeSpinachLot()
      if (active) {
        const patchResponse = await fetch(`${API}/api/lots/${active.lotId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ idempotencyKey: crypto.randomUUID(), quantity: String(originalAggregate), expiresOn: originalExpiresOn }),
        })
        check(patchResponse.ok, `cleanup restored Spinach lot to ${originalAggregate} g`)
      }
      const restored = await spinachAggregate()
      check(restored === originalAggregate, `server aggregate verified back at ${restored}`)
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
