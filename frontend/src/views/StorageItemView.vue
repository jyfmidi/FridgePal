<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppChip from '../components/AppChip.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { InsufficientQuantityError, fetchLots, type ApiLocation, type InventoryLot } from '../api/inventory'
import type { StorageLocation, Urgency } from '../features/storage/inventory'
import { useInventoryStore } from '../features/storage/inventoryStore'

/**
 * UI-03 — ingredient detail/edit. Entered with ?food=<foodKey>&location=<API casing>.
 * The aggregate quantity (from the hydrated store) leads; lot-level truth follows.
 * Every mutation goes through the store, which rehydrates the aggregate from the
 * server, so the tile on Storage reflects edits as soon as the user goes back.
 */
const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { inventory, updateLot, reduceStock, discardLotById } = useInventoryStore()

const foodKey = computed(() => String(route.query.food ?? ''))
const apiLocation = computed(() => String(route.query.location ?? 'FRIDGE').toUpperCase() as ApiLocation)
const locationKey = computed(() => apiLocation.value.toLowerCase() as StorageLocation)

const food = computed(() =>
  inventory.value.find((item) => item.foodKey === foodKey.value && item.location === locationKey.value),
)
const foodName = computed(() => (food.value ? t(food.value.nameKey) : foodKey.value))

const lots = ref<InventoryLot[]>([])
const lotsLoading = ref(true)
const loadFailed = ref(false)
const selectedLotId = ref<string | null>(null)

const selectedLot = computed(() => lots.value.find((lot) => lot.lotId === selectedLotId.value) ?? null)

const notice = ref('')
const errorMessage = ref('')
let noticeTimer: ReturnType<typeof setTimeout> | undefined

function showNotice(message: string) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => (notice.value = ''), 2500)
}

async function loadLots() {
  lotsLoading.value = true
  loadFailed.value = false
  try {
    const result = await fetchLots(foodKey.value, apiLocation.value)
    lots.value = [...result].sort((a, b) => Number(b.status === 'ACTIVE') - Number(a.status === 'ACTIVE'))
    if (!lots.value.some((lot) => lot.lotId === selectedLotId.value && lot.status === 'ACTIVE')) {
      selectedLotId.value = lots.value.find((lot) => lot.status === 'ACTIVE')?.lotId ?? null
    }
  } catch {
    loadFailed.value = true
  } finally {
    lotsLoading.value = false
  }
}

onMounted(loadLots)

function formatNumber(value: number): string {
  return new Intl.NumberFormat(locale.value, { maximumFractionDigits: 2 }).format(value)
}

/** Same label shape as the Storage tiles: bare number for pieces, number + unit otherwise. */
function quantityLabel(quantity: number, unit: string): string {
  const value = formatNumber(quantity)
  if (unit === 'piece') return value
  return `${value} ${t(`units.${unit}`, { count: quantity })}`
}

const unit = computed(() => food.value?.unit ?? lots.value.find((lot) => lot.status === 'ACTIVE')?.unit ?? 'piece')
const aggregate = computed(() => food.value?.quantity ?? 0)
const aggregateLabel = computed(() => quantityLabel(aggregate.value, unit.value))

const urgencyLabels: Record<Urgency, string> = {
  past: 'urgency.past',
  today: 'urgency.today',
  soon: 'urgency.oneToTwo',
  later: 'urgency.threeToFive',
  neutral: '',
}
const urgencyLabel = computed(() => {
  if (!food.value) return ''
  if (food.value.urgencyKey) return t(food.value.urgencyKey)
  const key = urgencyLabels[food.value.urgency]
  return key ? t(key) : ''
})

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(`${iso}T00:00:00`))
}

function lotDateLabel(lot: InventoryLot): string {
  return lot.expiresOn ? t('storageItem.expiresOn', { date: formatDate(lot.expiresOn) }) : t('storageItem.noExpiry')
}

/* ---- Edit lot ---- */

const editOpen = ref(false)
const editQuantity = ref(0)
const editLocation = ref<StorageLocation>('fridge')
const editExpiresOn = ref('')
const saving = ref(false)
const locations: StorageLocation[] = ['fridge', 'freezer', 'pantry']

function openEdit() {
  const lot = selectedLot.value
  if (!lot) return
  editQuantity.value = Number(lot.quantity)
  editLocation.value = lot.location.toLowerCase() as StorageLocation
  editExpiresOn.value = lot.expiresOn ?? ''
  editOpen.value = true
  reduceOpen.value = false
  discardArmed.value = false
}

/** After a mutation the food may be gone (fully used up, discarded, or moved away) — leave the view. */
async function afterMutation(): Promise<void> {
  if (!food.value) {
    await router.replace('/')
    return
  }
  await loadLots()
  showNotice(t('storageItem.updated'))
}

async function saveEdit() {
  const lot = selectedLot.value
  if (!lot || saving.value || editQuantity.value <= 0) return
  saving.value = true
  errorMessage.value = ''
  try {
    await updateLot(lot.lotId, {
      quantity: editQuantity.value,
      location: editLocation.value,
      expiresOn: editExpiresOn.value || null,
    })
    editOpen.value = false
    await afterMutation()
  } catch {
    errorMessage.value = t('storageItem.saveError')
  } finally {
    saving.value = false
  }
}

/* ---- Reduce stock ---- */

const reduceOpen = ref(false)
const reduceAmount = ref(0)
const reducing = ref(false)
const reduceError = ref('')

const reduceValid = computed(() => reduceAmount.value > 0 && reduceAmount.value <= aggregate.value)
const newTotalLabel = computed(() =>
  quantityLabel(Math.round((aggregate.value - reduceAmount.value) * 100) / 100, unit.value),
)

function openReduce() {
  reduceAmount.value = 0
  reduceError.value = ''
  reduceOpen.value = true
  editOpen.value = false
  discardArmed.value = false
}

async function confirmReduce() {
  if (!reduceValid.value || reducing.value) return
  reducing.value = true
  reduceError.value = ''
  try {
    await reduceStock({ foodKey: foodKey.value, location: locationKey.value, amount: reduceAmount.value, unit: unit.value })
    reduceOpen.value = false
    await afterMutation()
  } catch (error) {
    reduceError.value =
      error instanceof InsufficientQuantityError
        ? t('storageItem.insufficient', { quantity: aggregateLabel.value })
        : t('storageItem.saveError')
  } finally {
    reducing.value = false
  }
}

/* ---- Discard ---- */

const discardArmed = ref(false)
const discarding = ref(false)

async function confirmDiscard() {
  const lot = selectedLot.value
  if (!lot || discarding.value) return
  discarding.value = true
  errorMessage.value = ''
  try {
    await discardLotById(lot.lotId)
    discardArmed.value = false
    editOpen.value = false
    await afterMutation()
  } catch {
    errorMessage.value = t('storageItem.saveError')
    discardArmed.value = false
  } finally {
    discarding.value = false
  }
}
</script>

<template>
  <div class="item-view">
    <header class="task-header">
      <button type="button" :aria-label="t('common.back')" @click="router.push('/')">‹</button>
      <h1 class="task-header__title">
        <FoodToken v-if="food" :food-key="food.foodKey" :name="foodName" :size="30" />
        <span>{{ foodName }}</span>
      </h1>
      <span aria-hidden="true" />
    </header>

    <div v-if="notice" class="notice" role="status">
      <span>{{ notice }}</span>
      <button type="button" :aria-label="t('storageItem.dismiss')" @click="notice = ''">×</button>
    </div>

    <main v-if="food" class="item-content">
      <section class="hero-card">
        <strong class="hero-card__quantity">{{ aggregateLabel }}</strong>
        <div class="hero-card__meta">
          <span class="hero-card__location">{{ t(`storage.scopes.${food.location}`) }}</span>
          <span v-if="urgencyLabel" class="hero-card__urgency" :class="`hero-card__urgency--${food.urgency}`">
            {{ urgencyLabel }}
          </span>
        </div>
      </section>

      <section class="card">
        <h2>{{ t('storageItem.lots') }}</h2>
        <p v-if="loadFailed" class="inline-error">{{ t('storageItem.loadError') }}</p>
        <p v-else-if="!lotsLoading && !lots.length" class="inline-error">{{ t('storageItem.loadError') }}</p>
        <ul v-else class="lot-list">
          <li v-for="lot in lots" :key="lot.lotId">
            <button
              type="button"
              class="lot-row"
              :class="{ 'lot-row--selected': lot.lotId === selectedLotId, 'lot-row--depleted': lot.status !== 'ACTIVE' }"
              :disabled="lot.status !== 'ACTIVE'"
              :aria-label="t('storageItem.selectLot', { date: formatDate(lot.storedOn) })"
              @click="selectedLotId = lot.lotId"
            >
              <span class="lot-row__quantity">{{ quantityLabel(Number(lot.quantity), lot.unit) }}</span>
              <span class="lot-row__dates">
                <span>{{ t('storageItem.storedOn', { date: formatDate(lot.storedOn) }) }}</span>
                <span>{{ lotDateLabel(lot) }}</span>
              </span>
              <span class="lot-row__status">
                {{ lot.status === 'ACTIVE' ? t('storageItem.statusActive') : t('storageItem.statusDepleted') }}
              </span>
            </button>
          </li>
        </ul>
      </section>

      <section v-if="editOpen && selectedLot" class="card edit-section" aria-labelledby="edit-lot-heading">
        <h2 id="edit-lot-heading">{{ t('storageItem.editLot') }}</h2>
        <div class="form-row">
          <label>
            <span class="field-label">{{ t('storageItem.quantity') }}</span>
            <input v-model.number="editQuantity" class="text-input" type="number" min="0.01" step="0.01">
          </label>
          <label>
            <span class="field-label">{{ t('storageItem.expiresOnField') }}</span>
            <input v-model="editExpiresOn" class="text-input" type="date">
          </label>
        </div>
        <span class="field-label">{{ t('storageItem.location') }}</span>
        <div class="segmented-control">
          <AppChip v-for="item in locations" :key="item" :selected="editLocation === item" @toggle="editLocation = item">
            {{ t(`storage.scopes.${item}`) }}
          </AppChip>
        </div>
        <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
        <div class="edit-actions">
          <AppButton :disabled="saving || editQuantity <= 0" @click="saveEdit">
            {{ saving ? t('storageItem.saving') : t('storageItem.save') }}
          </AppButton>
          <AppButton variant="ghost" :disabled="saving" @click="editOpen = false">{{ t('common.done') }}</AppButton>
        </div>
      </section>

      <section v-if="reduceOpen" class="card edit-section" aria-labelledby="reduce-heading">
        <h2 id="reduce-heading">{{ t('storageItem.reduce') }}</h2>
        <label>
          <span class="field-label">{{ t('storageItem.reduceAmount') }}</span>
          <input v-model.number="reduceAmount" class="text-input" type="number" min="0.01" :max="aggregate" step="0.01">
        </label>
        <p class="reduce-preview" aria-live="polite">{{ t('storageItem.newTotal', { quantity: newTotalLabel }) }}</p>
        <p v-if="reduceError" class="inline-error">{{ reduceError }}</p>
        <div class="edit-actions">
          <AppButton :disabled="!reduceValid || reducing" @click="confirmReduce">
            {{ reducing ? t('storageItem.reducing') : t('storageItem.confirmReduce') }}
          </AppButton>
          <AppButton variant="ghost" :disabled="reducing" @click="reduceOpen = false">{{ t('common.done') }}</AppButton>
        </div>
      </section>

      <p v-if="errorMessage && !editOpen" class="inline-error">{{ errorMessage }}</p>
    </main>

    <main v-else class="item-content">
      <section class="card gone-card">
        <h2>{{ t('storageItem.goneTitle') }}</h2>
        <p>{{ t('storageItem.goneBody', { location: t(`storage.scopes.${locationKey}`) }) }}</p>
        <AppButton @click="router.push('/')">{{ t('storageItem.backToStorage') }}</AppButton>
      </section>
    </main>

    <footer v-if="food" class="action-bar sheet-up">
      <AppButton variant="secondary" size="small" :disabled="!selectedLot" @click="openEdit">
        {{ t('storageItem.edit') }}
      </AppButton>
      <AppButton size="small" @click="openReduce">{{ t('storageItem.reduce') }}</AppButton>
      <AppButton
        variant="ghost"
        size="small"
        class="discard-action"
        :disabled="!selectedLot || discarding"
        @click="discardArmed ? confirmDiscard() : (discardArmed = true)"
      >
        {{ discarding ? t('storageItem.discarding') : discardArmed ? t('storageItem.confirmDiscard') : t('storageItem.discard') }}
      </AppButton>
    </footer>
  </div>
</template>

<style scoped>
.item-view {
  width: min(100%, 720px);
  min-height: 100vh;
  padding-bottom: 92px;
  margin: 0 auto;
  background: var(--color-canvas);
}

.task-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: 44px 1fr 44px;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  text-align: center;
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
}

.task-header > button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-size: 2rem;
}

.task-header__title {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-size: var(--font-size-lg);
}

.task-header__title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice {
  position: sticky;
  z-index: var(--z-sticky);
  top: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: var(--space-3) var(--space-3) 0;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-on-primary);
  background: var(--color-primary);
  box-shadow: var(--shadow-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.notice button {
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  font-size: 1.1rem;
}

.item-content {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-3);
}

.card {
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.card h2 {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-base);
}

.hero-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.hero-card__quantity {
  font-size: var(--font-size-2xl, 2rem);
  font-variant-numeric: tabular-nums;
  font-weight: var(--font-weight-bold);
}

.hero-card__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.hero-card__urgency {
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  color: var(--color-urgency-neutral-ink);
  background: var(--color-urgency-neutral);
  font-weight: var(--font-weight-medium);
}

.hero-card__urgency--past {
  color: var(--color-urgency-past-ink);
  background: var(--color-urgency-past);
}

.hero-card__urgency--today {
  color: var(--color-urgency-today-ink);
  background: var(--color-urgency-today);
}

.hero-card__urgency--soon {
  color: var(--color-urgency-soon-ink);
  background: var(--color-urgency-soon);
}

.hero-card__urgency--later {
  color: var(--color-urgency-later-ink);
  background: var(--color-urgency-later);
}

.lot-list {
  display: grid;
  gap: var(--space-2);
  list-style: none;
}

.lot-row {
  display: flex;
  width: 100%;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--tap-target-min);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
  text-align: left;
}

.lot-row--selected {
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
}

.lot-row--depleted {
  opacity: 0.55;
}

.lot-row__quantity {
  min-width: 72px;
  font-variant-numeric: tabular-nums;
  font-weight: var(--font-weight-semibold);
}

.lot-row__dates {
  display: grid;
  flex: 1;
  min-width: 0;
  gap: 2px;
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.lot-row__status {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.field-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.text-input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.segmented-control {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-1);
  margin-bottom: var(--space-3);
}

.edit-actions {
  display: flex;
  gap: var(--space-2);
}

.edit-actions .app-button:first-child {
  flex: 1;
}

.reduce-preview {
  margin: var(--space-2) 0 var(--space-3);
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
}

.inline-error {
  margin: var(--space-2) 0;
  color: var(--color-urgency-past-ink);
  font-size: var(--font-size-sm);
}

.gone-card {
  display: grid;
  justify-items: start;
  gap: var(--space-2);
}

.gone-card p {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.action-bar {
  position: fixed;
  z-index: var(--z-sticky);
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

.action-bar .app-button--ghost.discard-action,
.discard-action {
  color: var(--color-urgency-past-ink);
}

.discard-action:hover:not(:disabled) {
  background-color: var(--color-urgency-past);
}
</style>
