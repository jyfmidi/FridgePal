/* Manual verification for the custom-food create flow (FR-LIB-003/FR-LIB-004).
 *
 * Run with the dev server on :5173 and the backend on :8000:
 *   node e2e/manual-check-kale.mjs
 *
 * Flow: search "Kale" in Add Food (not in the built-in catalog), create a
 * custom food, save it, assert the Storage tile renders with a "K" monogram,
 * reload to prove the server hydrate path keeps it, then clean up the lot via
 * the API discard endpoint.
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

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 390, height: 844 } })

try {
  await page.goto(`${BASE}/add-food`, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.clear()) // prove the server hydrate path, not a cache replay
  await page.reload({ waitUntil: 'networkidle' })

  await page.fill('#food-search', 'Kale')
  const createCard = page.locator('.create-custom')
  await createCard.waitFor()
  check((await createCard.textContent()).includes('Create "Kale"'), 'empty search shows a Create "Kale" card')
  check(await page.locator('.food-suggestion').count() === 0, 'no catalog suggestions for an unknown food')

  await createCard.click()
  const baseUnit = page.locator('input[list="base-unit-options"]')
  await baseUnit.waitFor()
  check(await baseUnit.inputValue() === 'g', 'custom food form defaults base unit to "g"')
  check(await page.locator('.create-custom--selected').count() === 1, 'create card shows selected state after tap')

  await page.locator('input[type="number"]').fill('200')
  await page.getByRole('button', { name: 'Save food' }).click()
  await page.waitForURL(`${BASE}/`)

  const tile = page.locator('.inventory-grid .storage-tile', { hasText: 'Kale' })
  await tile.waitFor()
  check(true, 'Storage shows a "Kale" tile after save')
  check((await tile.locator('.food-token__monogram').textContent()) === 'K', 'tile renders the "K" monogram (unknown foodKey)')
  const tileText = await tile.textContent()
  const tileQuantity = Number(tileText.match(/[\d.]+/)?.[0])
  check(tileQuantity >= 200, `tile shows the saved quantity (got ${tileQuantity}; reruns add 200 each if cleanup is unavailable)`)

  await page.reload({ waitUntil: 'networkidle' })
  const tileAfterReload = page.locator('.inventory-grid .storage-tile', { hasText: 'Kale' })
  await tileAfterReload.waitFor()
  check(true, '"Kale" tile persists after reload (server hydrate)')
  check((await tileAfterReload.locator('.food-token__monogram').textContent()) === 'K', 'monogram survives hydrate')
} finally {
  await browser.close()
}

// Cleanup: discard the Kale lots created above (compensating event, reversible).
// The discard routes exist in the current backend source, but a running server
// started before they were added (openapi shows only check-in/storage/health)
// returns 404 — in that case the lots stay and are noted, not silently ignored.
async function fetchLots() {
  for (const path of ['/api/inventory/lots', '/api/lots']) {
    const response = await fetch(`${API}${path}?foodKey=custom:kale&location=FRIDGE`)
    if (response.ok) return response.json()
  }
  return null
}

const lotsBody = await fetchLots()
if (lotsBody) {
  for (const lot of lotsBody.lots) {
    const discard = await fetch(`${API}/api/lots/${lot.lotId}/discard`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ idempotencyKey: crypto.randomUUID() }),
    })
    console.log(`${discard.ok ? 'ok' : 'FAIL'} - discarded lot ${lot.lotId}`)
  }
  if (lotsBody.lots.length === 0) console.log('ok - no Kale lots left to discard')
} else {
  console.log('NOTE - running backend has no lot discard route; Kale test lots left in the database (restart the backend to get /api/lots/{id}/discard, then rerun to clean up)')
}

if (failures > 0) {
  console.error(`\n${failures} check(s) failed`)
  process.exit(1)
}
console.log('\nall checks passed')
