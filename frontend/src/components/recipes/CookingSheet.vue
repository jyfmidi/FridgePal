<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { cookingCommit, cookingPreview, StalePreviewError } from '../../api/inventory'
import type { InventoryFood } from '../../features/storage/inventory'
import { useInventoryStore } from '../../features/storage/inventoryStore'
import FoodToken from '../food-token/FoodToken.vue'
import StorageIngredientPicker from './StorageIngredientPicker.vue'

/** One recipe ingredient handed to the sheet, with the effective (portion-scaled) amount. */
export interface CookingSheetIngredient {
  id: string
  nameKey: string
  foodKey?: string
  amount: string
}

interface CookingLine {
  key: string
  foodKey: string
  nameKey: string
  /** Original recipe text, shown when it cannot be prefilled into storage units. */
  recipeAmount: string
  /** Editable numeric amount in storage units; blank means "not deducted". */
  amount: string
  unit: string
  included: boolean
}

const props = defineProps<{
  open: boolean
  recipeName: string
  ingredients: CookingSheetIngredient[]
  foods: InventoryFood[]
}>()

const emit = defineEmits<{
  close: []
  cooked: []
}>()

const { t } = useI18n()
const { hydrateFromServer } = useInventoryStore()

const lines = ref<CookingLine[]>([])
const untracked = ref<{ id: string; nameKey: string; amount: string }[]>([])
const pickerOpen = ref(false)
const submitting = ref(false)
const staleNotice = ref(false)
const errorMessage = ref('')
const sheetElement = ref<HTMLElement | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)
let previousBodyOverflow = ''

/** Aggregate availability per foodKey+unit across every storage location. */
const availability = computed(() => {
  const totals = new Map<string, number>()
  for (const food of props.foods) {
    const key = `${food.foodKey}|${food.unit}`
    totals.set(key, (totals.get(key) ?? 0) + food.quantity)
  }
  return totals
})

/** Inventory ids already on a line, so the picker cannot re-add them. */
const lineFoodIds = computed(
  () =>
    new Set(
      lines.value
        .map((line) => props.foods.find((food) => food.foodKey === line.foodKey)?.id)
        .filter((id): id is string => Boolean(id)),
    ),
)

const hasDeductions = computed(() => lines.value.some((line) => line.included && Number(line.amount) > 0))

function parseAmount(raw: string): { value: string; unit: string } {
  const match = raw.trim().match(/^([0-9]+(?:\.[0-9]+)?)\s*(.*)$/)
  return { value: match?.[1] ?? '', unit: match?.[2]?.trim() ?? '' }
}

function buildLines() {
  const nextLines: CookingLine[] = []
  const nextUntracked: { id: string; nameKey: string; amount: string }[] = []
  for (const ingredient of props.ingredients) {
    if (!ingredient.foodKey) {
      nextUntracked.push({ id: ingredient.id, nameKey: ingredient.nameKey, amount: ingredient.amount })
      continue
    }
    const stored = props.foods.find((food) => food.foodKey === ingredient.foodKey)
    const parsed = parseAmount(ingredient.amount)
    const unit = stored?.unit ?? parsed.unit ?? 'g'
    // Prefill only when the recipe unit matches the storage unit; otherwise the
    // user types the storage-unit amount themselves; Fridgital never guesses a conversion.
    const prefill = stored && parsed.value && (!parsed.unit || parsed.unit === stored.unit) ? parsed.value : ''
    nextLines.push({
      key: ingredient.id,
      foodKey: ingredient.foodKey,
      nameKey: ingredient.nameKey,
      recipeAmount: prefill ? '' : ingredient.amount,
      amount: prefill,
      unit,
      included: true,
    })
  }
  lines.value = nextLines
  untracked.value = nextUntracked
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      buildLines()
      submitting.value = false
      staleNotice.value = false
      errorMessage.value = ''
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      await nextTick()
      closeButton.value?.focus()
    } else {
      document.body.style.overflow = previousBodyOverflow
    }
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow
})

function availableFor(line: CookingLine): number {
  return availability.value.get(`${line.foodKey}|${line.unit}`) ?? 0
}

function hasShortfall(line: CookingLine): boolean {
  return line.included && Number(line.amount) > availableFor(line)
}

function hintFor(line: CookingLine): string {
  const available = availableFor(line)
  if (available === 0) return t('cooking.noneAvailable')
  const quantity = `${available} ${line.unit}`
  return hasShortfall(line)
    ? t('cooking.shortfallHint', { available: quantity })
    : t('cooking.availableHint', { quantity })
}

function toggleLine(line: CookingLine) {
  line.included = !line.included
}

function addExtraFoods(foodIds: string[]) {
  for (const foodId of foodIds) {
    const food = props.foods.find((item) => item.id === foodId)
    if (!food || lines.value.some((line) => line.foodKey === food.foodKey)) continue
    lines.value.push({
      key: `extra-${food.id}`,
      foodKey: food.foodKey,
      nameKey: food.nameKey,
      recipeAmount: '',
      amount: '',
      unit: food.unit,
      included: true,
    })
  }
  pickerOpen.value = false
}

function close() {
  if (submitting.value) return
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    close()
    return
  }
  if (event.key !== 'Tab') return
  const root = sheetElement.value
  if (!root) return
  const focusable = Array.from(
    root.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled)'),
  )
  if (focusable.length === 0) return
  const first = focusable[0]!
  const last = focusable[focusable.length - 1]!
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

async function updateStorage() {
  errorMessage.value = ''
  staleNotice.value = false
  const items = lines.value
    .filter((line) => line.included && Number(line.amount) > 0)
    .map((line) => ({ foodKey: line.foodKey, amount: String(Number(line.amount)), unit: line.unit }))
  if (items.length === 0) return
  submitting.value = true
  try {
    // Fresh lot allocations, then one atomic commit in the same user gesture.
    // The backend caps each line at availability, so shortfalls deduct less.
    const preview = await cookingPreview(items)
    await cookingCommit({
      idempotencyKey: crypto.randomUUID(),
      sessionName: props.recipeName,
      lines: preview.lines
        .filter((line) => line.allocations.length > 0)
        .map((line) => ({ foodKey: line.foodKey, allocations: line.allocations })),
    })
    emit('cooked')
  } catch (error) {
    if (error instanceof StalePreviewError) {
      // FR-COOK-007: inventory moved under the preview; refresh the hints and
      // make the user confirm again against the new numbers.
      staleNotice.value = true
      await hydrateFromServer()
    } else {
      errorMessage.value = t('cooking.updateError')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="cooking-overlay" @click.self="close" @keydown="onKeydown">
      <section ref="sheetElement" class="cooking-sheet sheet-up" role="dialog" aria-modal="true" aria-labelledby="cooking-sheet-title">
        <header class="cooking-sheet__header">
          <button ref="closeButton" type="button" :aria-label="t('common.back')" @click="close">×</button>
          <div>
            <h2 id="cooking-sheet-title">{{ t('cooking.title') }}</h2>
            <span>{{ recipeName }}</span>
          </div>
          <span aria-hidden="true" />
        </header>

        <div class="cooking-sheet__body">
          <p class="cooking-sheet__explainer">{{ t('cooking.oldestFirst') }}</p>
          <p v-if="staleNotice" class="cooking-sheet__stale" role="alert">{{ t('cooking.staleNotice') }}</p>
          <p v-if="errorMessage" class="cooking-sheet__error" role="alert">{{ errorMessage }}</p>

          <ul v-if="lines.length" class="cooking-lines">
            <li
              v-for="line in lines"
              :key="line.key"
              class="cooking-line"
              :class="{ 'cooking-line--excluded': !line.included, 'cooking-line--shortfall': hasShortfall(line) || availableFor(line) === 0 }"
            >
              <FoodToken :food-key="line.foodKey" :name="t(line.nameKey)" :size="38" />
              <div class="cooking-line__main">
                <span class="cooking-line__name">{{ t(line.nameKey) }}</span>
                <small>{{ hintFor(line) }}</small>
                <small v-if="line.recipeAmount">{{ t('cooking.recipeAmount', { amount: line.recipeAmount }) }}</small>
              </div>
              <label class="cooking-line__amount">
                <span class="sr-only">{{ t('cooking.amountFor', { name: t(line.nameKey) }) }}</span>
                <input v-model="line.amount" type="number" min="0" step="any" inputmode="decimal" :disabled="!line.included">
                <span>{{ line.unit }}</span>
              </label>
              <button
                type="button"
                class="cooking-line__toggle"
                :aria-pressed="line.included"
                :aria-label="t('cooking.toggleLine', { name: t(line.nameKey) })"
                @click="toggleLine(line)"
              >
                {{ t(line.included ? 'cooking.included' : 'cooking.excluded') }}
              </button>
            </li>
          </ul>

          <button type="button" class="cooking-sheet__add" @click="pickerOpen = true">
            <span aria-hidden="true">＋</span>
            {{ t('cooking.addFood') }}
          </button>

          <section v-if="untracked.length" class="cooking-untracked">
            <h3>{{ t('cooking.notTracked') }}</h3>
            <ul>
              <li v-for="item in untracked" :key="item.id">
                <FoodToken :name="t(item.nameKey)" :size="30" />
                <span>{{ t(item.nameKey) }}</span>
                <small>{{ item.amount }}</small>
              </li>
            </ul>
            <p>{{ t('cooking.notTrackedHint') }}</p>
          </section>
        </div>

        <footer class="cooking-sheet__footer">
          <p>{{ t('cooking.nothingChanges') }}</p>
          <button type="button" :disabled="submitting || !hasDeductions" @click="updateStorage">
            {{ t(submitting ? 'cooking.updating' : 'cooking.updateStorage') }}
          </button>
        </footer>
      </section>
    </div>
    <StorageIngredientPicker
      :open="pickerOpen"
      :foods="foods"
      :ingredient-ids="lineFoodIds"
      @close="pickerOpen = false"
      @confirm="addExtraFoods"
    />
  </Teleport>
</template>

<style scoped>
.cooking-overlay {
  position: fixed;
  z-index: var(--z-sheet);
  inset: 0;
  display: grid;
  align-items: end;
  background: rgb(8 18 38 / 0.42);
}

.cooking-sheet {
  display: grid;
  width: 100%;
  max-height: calc(100dvh - var(--safe-area-top) - 24px);
  grid-template-rows: auto minmax(0, 1fr) auto;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  background: var(--color-canvas);
  box-shadow: var(--shadow-overlay);
  overflow: hidden;
}

.cooking-sheet__header {
  display: grid;
  min-height: 68px;
  grid-template-columns: 64px 1fr 64px;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  text-align: center;
}

.cooking-sheet__header button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-size: 1.8rem;
  font-weight: var(--font-weight-semibold);
}

.cooking-sheet__header h2 {
  font-size: var(--font-size-lg);
}

.cooking-sheet__header span {
  display: block;
  overflow: hidden;
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cooking-sheet__body {
  display: grid;
  align-content: start;
  gap: var(--space-3);
  padding: var(--space-3);
  overflow-y: auto;
}

.cooking-sheet__explainer {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  text-align: center;
}

.cooking-sheet__stale,
.cooking-sheet__error {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.cooking-sheet__stale {
  color: var(--color-primary-hover);
  background: var(--color-primary-softer);
}

.cooking-sheet__error {
  color: var(--color-danger-ink);
  background: var(--color-danger-soft);
}

.cooking-lines {
  display: grid;
  gap: var(--space-2);
}

.cooking-line {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.cooking-line--shortfall {
  box-shadow: inset 0 0 0 1px var(--color-danger-edge);
}

.cooking-line--excluded {
  opacity: 0.55;
}

.cooking-line__main {
  display: grid;
  min-width: 0;
}

.cooking-line__name {
  overflow: hidden;
  font-weight: var(--font-weight-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cooking-line__main small {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.cooking-line--shortfall .cooking-line__main small:first-of-type {
  color: var(--color-danger-ink);
}

.cooking-line__amount {
  display: flex;
  grid-column: 1 / -2;
  align-items: center;
  gap: var(--space-2);
}

.cooking-line__amount input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.cooking-line__amount span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.cooking-line__toggle {
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border-radius: var(--radius-full);
  color: var(--color-on-primary);
  background: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.cooking-line__toggle[aria-pressed='false'] {
  color: var(--color-primary);
  background: var(--color-primary-softer);
}

.cooking-sheet__add {
  display: flex;
  min-height: 52px;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px dashed var(--color-primary);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.cooking-untracked {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.cooking-untracked h3 {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.cooking-untracked ul {
  display: grid;
  gap: var(--space-2);
}

.cooking-untracked li {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.cooking-untracked li span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cooking-untracked li small,
.cooking-untracked p {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.cooking-sheet__footer {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

.cooking-sheet__footer p {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  text-align: center;
}

.cooking-sheet__footer button {
  min-height: 52px;
  border-radius: var(--radius-lg);
  color: var(--color-on-primary);
  background: var(--color-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.cooking-sheet__footer button:disabled {
  opacity: 0.45;
}

@media (min-width: 720px) {
  .cooking-overlay {
    place-items: center;
    padding: var(--space-8);
  }

  .cooking-sheet {
    width: min(640px, 100%);
    max-height: calc(100dvh - 64px);
    border-radius: var(--radius-xl);
  }

  .cooking-line {
    grid-template-columns: auto minmax(0, 1fr) 160px auto;
  }

  .cooking-line__amount {
    grid-column: auto;
  }

  .cooking-sheet__footer {
    grid-template-columns: 1fr auto;
    align-items: center;
  }

  .cooking-sheet__footer p {
    text-align: left;
  }

  .cooking-sheet__footer button {
    min-width: 220px;
    padding: 0 var(--space-5);
  }
}
</style>
