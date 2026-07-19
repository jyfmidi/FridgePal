/* Manual verification for the cooking reconciliation flow (UI-10,
 * FR-COOK-001..007, FR-RCP-001).
 *
 * Run with the dev server on :5173 and the backend on :8000:
 *   node e2e/manual-check-cook.mjs
 *
 * Flow: open the demo saved recipe "Creamy spinach & mushroom penne" from
 * Recipes, tap "Cook this", assert the "What did you use?" sheet, exclude
 * Mushrooms, edit the Spinach amount, confirm "Update storage", and assert
 * the Spinach aggregate dropped by exactly the confirmed amount while
 * Mushrooms stayed unchanged. The deducted amount is checked back in
 * afterwards so the demo data stays sane. Also verifies zh-CN rendering.
 */
import { chromium } from '@playwright/test'

const BASE = 'http://localhost:5173'
const API = 'http://localhost:8000'
const SPINACH_DEDUCT = 50

let failures = 0
function check(condition, message) {
  if (condition) {
    console.log(`ok - ${message}`)
  } else {
    failures += 1
    console.error(`FAIL - ${message}`)
  }
}

async function aggregates() {
  const response = await fetch(`${API}/api/storage`)
  const body = await response.json()
  const totals = new Map()
  for (const item of body.inventory) {
    totals.set(item.foodKey, (totals.get(item.foodKey) ?? 0) + Number(item.quantity))
  }
  return totals
}

const before = await aggregates()
console.log(`before: spinach=${before.get('spinach')} mushrooms=${before.get('mushrooms')}`)

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 390, height: 844 } })

try {
  await page.goto(`${BASE}/recipes`, { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.clear()) // fall back to the deterministic demo recipes
  await page.reload({ waitUntil: 'networkidle' })

  // Open the saved recipe that uses storage foods, then start cooking.
  const card = page.locator('.saved-recipe-card', { hasText: 'Creamy spinach & mushroom penne' }).first()
  await card.getByRole('button', { name: 'Cook again' }).click()
  await page.waitForURL(/\/recipes\/editor/)
  await page.getByRole('button', { name: 'Cook this' }).click()

  // Sheet content (FR-COOK-001, FR-COOK-003).
  const sheet = page.locator('.cooking-sheet')
  await sheet.waitFor()
  check(await sheet.locator('h2').textContent() === 'What did you use?', 'sheet title is "What did you use?"')
  check((await sheet.textContent()).includes("We'll use the oldest items first"), 'sheet explains oldest-first allocation')
  check((await sheet.textContent()).includes('Nothing changes until you confirm'), 'sheet states the mutation gate')

  const spinachLine = sheet.locator('.cooking-line', { hasText: 'Spinach' })
  const mushroomLine = sheet.locator('.cooking-line', { hasText: 'Mushrooms' })
  const garlicLine = sheet.locator('.cooking-line', { hasText: 'Garlic' })
  check((await spinachLine.locator('input').inputValue()) === '200', 'Spinach prefilled with scaled 200')
  check((await mushroomLine.locator('input').inputValue()) === '120', 'Mushrooms prefilled with scaled 120')
  check((await spinachLine.textContent()).includes('available'), 'tracked line shows an availability hint')
  check((await garlicLine.locator('input').inputValue()) === '', 'unit-mismatched line (2 cloves vs bulbs) is not prefilled')
  check((await garlicLine.textContent()).includes('Recipe: 2 cloves'), 'unit-mismatched line shows the recipe amount')

  // FR-COOK-002: exclude Mushrooms, edit the Spinach amount.
  await mushroomLine.getByRole('button', { name: 'Include or exclude Mushrooms' }).click()
  check((await mushroomLine.locator('.cooking-line__toggle').textContent()).includes('Excluded'), 'excluded line shows Excluded state')
  await spinachLine.locator('input').fill(String(SPINACH_DEDUCT))

  // FR-COOK-003/006: single mutation gate.
  await sheet.getByRole('button', { name: 'Update storage' }).click()
  await page.locator('.notice', { hasText: 'Storage updated' }).waitFor()
  check(true, 'editor shows "Storage updated" feedback')
  check(await sheet.count() === 0, 'sheet closes after a successful commit')

  const after = await aggregates()
  console.log(`after:  spinach=${after.get('spinach')} mushrooms=${after.get('mushrooms')}`)
  check(after.get('spinach') === before.get('spinach') - SPINACH_DEDUCT, `spinach decreased by exactly ${SPINACH_DEDUCT}`)
  check(after.get('mushrooms') === before.get('mushrooms'), 'excluded mushrooms unchanged')

  // Storage page reflects the deduction (aggregate tile, no lot badges).
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
  const tileText = await page.locator('.inventory-grid .storage-tile', { hasText: 'Spinach' }).textContent()
  check(tileText.includes(String(after.get('spinach'))), `Storage tile shows the new aggregate (${after.get('spinach')})`)

  // zh-CN rendering of the sheet (desktop viewport: the locale toggle is
  // hidden on mobile, and this also exercises the centered-dialog layout).
  // The locale lives in the app session, so navigate client-side after
  // toggling — a full reload would reset it to English.
  await page.setViewportSize({ width: 900, height: 800 })
  await page.locator('.locale-action').click()
  await page.getByRole('link', { name: '菜谱' }).click()
  await page.waitForURL(/\/recipes/)
  await page.locator('.saved-recipe-card', { hasText: 'Creamy spinach & mushroom penne' }).first()
    .getByRole('button', { name: '再做一次' }).click()
  await page.waitForURL(/\/recipes\/editor/)
  await page.getByRole('button', { name: '开始做菜' }).click()
  const sheetZh = page.locator('.cooking-sheet')
  await sheetZh.waitFor()
  check(await sheetZh.locator('h2').textContent() === '这次做菜用了什么？', 'zh-CN sheet title renders')
  check((await sheetZh.textContent()).includes('会优先消耗最早存入的食材'), 'zh-CN oldest-first copy renders')
  check((await sheetZh.textContent()).includes('确认之前库存不会有任何变化'), 'zh-CN mutation-gate copy renders')
  check((await sheetZh.textContent()).includes('菠菜'), 'zh-CN food names render')
  await sheetZh.getByRole('button', { name: '返回' }).click() // cancel: no mutation
  check(await sheetZh.count() === 0, 'closing the zh-CN sheet cancels without mutation')

  const cancelled = await aggregates()
  check(cancelled.get('spinach') === after.get('spinach'), 'cancel did not deduct anything')
} catch (error) {
  failures += 1
  console.error(`FAIL - browser flow threw: ${error}`)
} finally {
  await browser.close()
}

// Restore the deducted spinach so the demo data stays sane.
const restore = await fetch(`${API}/api/inventory/check-in`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    idempotencyKey: crypto.randomUUID(),
    foodKey: 'spinach',
    names: { en: 'Spinach', 'zh-CN': '菠菜' },
    quantity: String(SPINACH_DEDUCT),
    unit: 'g',
    location: 'FRIDGE',
    storedOn: new Date().toISOString().slice(0, 10),
    expirySource: 'NONE',
  }),
})
check(restore.ok, `restored ${SPINACH_DEDUCT} g spinach via check-in`)
const restored = await aggregates()
check(restored.get('spinach') === before.get('spinach'), 'spinach aggregate back to the original value')

if (failures > 0) {
  console.error(`\n${failures} check(s) failed`)
  process.exit(1)
}
console.log('\nall checks passed')
