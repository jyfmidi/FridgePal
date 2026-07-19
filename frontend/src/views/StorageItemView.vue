<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppIcon from '../components/AppIcon.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import LocationBadge from '../components/LocationBadge.vue'
import LocationFilterBar from '../components/LocationFilterBar.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { InsufficientQuantityError, fetchLots, type ApiLocation, type InventoryLot } from '../api/inventory'
import {
  compatibleInventoryUnits,
  convertInventoryQuantity,
  isInventoryUnit,
  normalizeLegacyInventoryUnit,
  roundInventoryQuantity,
  type InventoryUnit,
  type StorageLocation,
  type Urgency,
} from '../features/storage/inventory'
import { useInventoryStore } from '../features/storage/inventoryStore'

/**
 * UI-03 — ingredient detail/edit. Entered with ?food=<foodKey>&location=<API casing>.
 * A focused single-food editor: one quantity control (decrease = FEFO reduceStock,
 * increase = updateLot on the earliest ACTIVE lot), a use-by date bound to that same
 * lot, and a collapsed lots disclosure for per-lot editing, moving, and discarding.
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

/** Earliest-stored ACTIVE lot — the target for quantity increases and the use-by date. */
const earliestLot = computed(() =>
  lots.value
    .filter((lot) => lot.status === 'ACTIVE')
    .sort((a, b) => a.storedOn.localeCompare(b.storedOn))[0] ?? null,
)

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

onMounted(async () => {
  await loadLots()
  syncDrafts()
})

function formatNumber(value: number): string {
  return new Intl.NumberFormat(locale.value, { maximumFractionDigits: 2 }).format(value)
}

const localizedUnitKeys = new Set(['g', 'kg', 'ml', 'l', 'piece'])

function unitLabel(value: string, quantity: number): string {
  return localizedUnitKeys.has(value) ? t(`units.${value}`, quantity) : value
}

/** Same explicit value-plus-unit label shape as the Storage tiles. */
function quantityLabel(quantity: number, unit: string): string {
  const value = formatNumber(quantity)
  return `${value} ${unitLabel(unit, quantity)}`
}

function canonicalUnit(value: string): InventoryUnit {
  const normalized = normalizeLegacyInventoryUnit(value)
  return isInventoryUnit(normalized) ? normalized : 'piece'
}

const unit = computed<InventoryUnit>(() =>
  canonicalUnit(food.value?.unit ?? lots.value.find((lot) => lot.status === 'ACTIVE')?.unit ?? 'piece'),
)
const aggregate = computed(() => food.value?.quantity ?? 0)

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
const urgencyIcon = computed<'clock' | 'tombstone'>(() => (food.value?.urgency === 'past' ? 'tombstone' : 'clock'))

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat(locale.value, { dateStyle: 'medium' }).format(new Date(`${iso}T00:00:00`))
}

function lotDateLabel(lot: InventoryLot): string {
  return lot.expiresOn ? t('storageItem.expiresOn', { date: formatDate(lot.expiresOn) }) : t('storageItem.noExpiry')
}

/* ---- Direct inventory drafts ---- */

const quantityDraft = ref(0)
const unitDraft = ref<InventoryUnit>('piece')
const storedDateDraft = ref('')
const dateDraft = ref('')
const applying = ref(false)
const draftReady = ref(false)
const unitOptions = computed(() => compatibleInventoryUnits(unit.value))

function syncDrafts() {
  quantityDraft.value = aggregate.value
  unitDraft.value = unit.value
  storedDateDraft.value = earliestLot.value?.storedOn ?? ''
  dateDraft.value = earliestLot.value?.expiresOn ?? ''
  draftReady.value = true
}

const delta = computed(() => {
  if (!draftReady.value || !Number.isFinite(quantityDraft.value)) return 0
  const currentInDraftUnit = convertInventoryQuantity(aggregate.value, unit.value, unitDraft.value)
  return roundInventoryQuantity(quantityDraft.value - currentInDraftUnit)
})
const unitChanged = computed(() => draftReady.value && unitDraft.value !== unit.value)
const storedDateChanged = computed(() => storedDateDraft.value !== (earliestLot.value?.storedOn ?? ''))
const dateChanged = computed(() => dateDraft.value !== (earliestLot.value?.expiresOn ?? ''))
const dirty = computed(() => draftReady.value && (delta.value !== 0 || unitChanged.value || storedDateChanged.value || dateChanged.value))
const formValid = computed(
  () => draftReady.value && Number.isFinite(quantityDraft.value) && quantityDraft.value > 0 && storedDateDraft.value.length > 0,
)

function chooseDraftUnit(event: Event) {
  const nextUnit = (event.target as HTMLSelectElement).value
  if (!isInventoryUnit(nextUnit) || nextUnit === unitDraft.value) return
  quantityDraft.value = roundInventoryQuantity(
    convertInventoryQuantity(quantityDraft.value, unitDraft.value, nextUnit),
  )
  unitDraft.value = nextUnit
}

/** Keep drafts aligned with server truth until the user starts editing. */
watch([aggregate, earliestLot, unit], () => {
  if (!dirty.value) syncDrafts()
})

function resetDrafts() {
  errorMessage.value = ''
  syncDrafts()
}

/** After a mutation the food may be gone (fully used up, discarded, or moved away) — leave the view. */
async function afterMutation(): Promise<void> {
  if (!food.value) {
    await router.replace('/')
    return
  }
  await loadLots()
  syncDrafts()
  showNotice(t('storageItem.updated'))
}

async function applyChanges() {
  if (!dirty.value || applying.value) return
  if (!formValid.value) {
    errorMessage.value = t('storageItem.invalidForm')
    return
  }
  applying.value = true
    errorMessage.value = ''
  try {
    const lot = earliestLot.value
    const quantityUp = delta.value > 0 && lot
      ? roundInventoryQuantity(
          convertInventoryQuantity(Number(lot.quantity), unit.value, unitDraft.value) + delta.value,
        )
      : undefined
    if (lot && (quantityUp !== undefined || unitChanged.value || storedDateChanged.value || dateChanged.value)) {
      await updateLot(lot.lotId, {
        ...(quantityUp !== undefined ? { quantity: quantityUp } : {}),
        ...(unitChanged.value ? { unit: unitDraft.value } : {}),
        ...(storedDateChanged.value ? { storedOn: storedDateDraft.value } : {}),
        ...(dateChanged.value ? { expiresOn: dateDraft.value || null } : {}),
      })
    }
    if (delta.value < 0) {
      await reduceStock({
        foodKey: foodKey.value,
        location: locationKey.value,
        amount: -delta.value,
        unit: unitDraft.value,
      })
    }
    await afterMutation()
  } catch (error) {
    errorMessage.value =
      error instanceof InsufficientQuantityError
        ? t('storageItem.insufficient', { quantity: quantityLabel(aggregate.value, unit.value) })
        : t('storageItem.saveError')
    await loadLots()
    syncDrafts()
  } finally {
    applying.value = false
  }
}

/* ---- Lots disclosure: per-lot edit ---- */

const editOpen = ref(false)
const editQuantity = ref(0)
const editUnit = ref<InventoryUnit>('piece')
const editLocation = ref<StorageLocation>('fridge')
const editStoredOn = ref('')
const editExpiresOn = ref('')
const saving = ref(false)
const editUnitOptions = computed(() =>
  compatibleInventoryUnits(canonicalUnit(selectedLot.value?.unit ?? editUnit.value)),
)

function openEdit() {
  const lot = selectedLot.value
  if (!lot) return
  editQuantity.value = Number(lot.quantity)
  editUnit.value = canonicalUnit(lot.unit)
  editLocation.value = lot.location.toLowerCase() as StorageLocation
  editStoredOn.value = lot.storedOn
  editExpiresOn.value = lot.expiresOn ?? ''
  editOpen.value = true
  discardArmed.value = false
}

function chooseEditUnit(event: Event) {
  const nextUnit = (event.target as HTMLSelectElement).value
  if (!isInventoryUnit(nextUnit) || nextUnit === editUnit.value) return
  editQuantity.value = roundInventoryQuantity(
    convertInventoryQuantity(editQuantity.value, editUnit.value, nextUnit),
  )
  editUnit.value = nextUnit
}

async function saveEdit() {
  const lot = selectedLot.value
  if (!lot || saving.value || editQuantity.value <= 0 || !editStoredOn.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    await updateLot(lot.lotId, {
      quantity: editQuantity.value,
      unit: editUnit.value,
      location: editLocation.value,
      storedOn: editStoredOn.value,
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

/* ---- Lots disclosure: two-step discard ---- */

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
    <AppTaskHeader :title="foodName" :back-label="t('common.back')" @back="router.push('/')" />

    <div v-if="notice" class="notice" role="status">
      <span>{{ notice }}</span>
      <button type="button" :aria-label="t('storageItem.dismiss')" @click="notice = ''">×</button>
    </div>

    <main v-if="food" class="item-content stagger-in">
      <section class="hero-card">
        <FoodToken :food-key="food.foodKey" :name="foodName" :size="76" />
        <div class="hero-card__identity">
          <h2 class="hero-card__name">{{ foodName }}</h2>
          <div class="hero-card__badges">
            <LocationBadge :location="food.location" />
            <span v-if="urgencyLabel" class="hero-card__urgency" :class="`hero-card__urgency--${food.urgency}`">
              <AppIcon :name="urgencyIcon" :size="15" />
              {{ urgencyLabel }}
            </span>
            <span v-if="earliestLot" class="hero-card__stored">{{ t('storageItem.storedOn', { date: formatDate(earliestLot.storedOn) }) }}</span>
          </div>
        </div>
      </section>

      <section class="card inventory-form" aria-labelledby="inventory-details-heading">
        <h2 id="inventory-details-heading" class="section-title">
          <AppIcon name="storage" :size="21" />
          {{ t('storageItem.details') }}
        </h2>
        <div class="inventory-form__grid">
          <label class="field-card">
            <span class="field-card__label">{{ t('storageItem.quantity') }}</span>
            <input v-model.number="quantityDraft" class="text-input field-card__input" type="number" min="0.01" step="0.01">
          </label>
          <label class="field-card">
            <span class="field-card__label"><AppIcon name="unit" :size="18" />{{ t('storageItem.unit') }}</span>
            <select :value="unitDraft" class="text-input field-card__input" @change="chooseDraftUnit">
              <option v-for="item in unitOptions" :key="item" :value="item">{{ t(`units.${item}`, quantityDraft) }}</option>
            </select>
          </label>
          <label class="field-card">
            <span class="field-card__label"><AppIcon name="calendar" :size="18" />{{ t('storageItem.storedOnField') }}</span>
            <input v-model="storedDateDraft" class="text-input field-card__input" type="date">
          </label>
          <label class="field-card">
            <span class="field-card__label"><AppIcon name="calendar-check" :size="18" />{{ t('storageItem.expiresOnField') }}</span>
            <input v-model="dateDraft" class="text-input field-card__input" type="date">
          </label>
        </div>
      </section>

      <details class="card lots-disclosure">
        <summary>
          <span>{{ t('storageItem.lotsTitle', { count: lots.length }) }}</span>
          <span class="lots-disclosure__chevron" aria-hidden="true">›</span>
        </summary>
        <p v-if="loadFailed" class="inline-error">{{ t('storageItem.loadError') }}</p>
        <p v-else-if="!lotsLoading && !lots.length" class="inline-error">{{ t('storageItem.loadError') }}</p>
        <template v-else>
          <ul class="lot-list">
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

          <section v-if="editOpen && selectedLot" class="edit-section" aria-labelledby="edit-lot-heading">
            <h3 id="edit-lot-heading">{{ t('storageItem.editLot') }}</h3>
            <div class="form-row">
              <label>
                <span class="field-label">{{ t('storageItem.quantity') }}</span>
                <input v-model.number="editQuantity" class="text-input" type="number" min="0.01" step="0.01">
              </label>
              <label>
                <span class="field-label">{{ t('storageItem.unit') }}</span>
                <select :value="editUnit" class="text-input" @change="chooseEditUnit">
                  <option v-for="item in editUnitOptions" :key="item" :value="item">{{ t(`units.${item}`, editQuantity) }}</option>
                </select>
              </label>
            </div>
            <div class="form-row">
              <label>
                <span class="field-label">{{ t('storageItem.storedOnField') }}</span>
                <input v-model="editStoredOn" class="text-input" type="date">
              </label>
              <label>
                <span class="field-label">{{ t('storageItem.expiresOnField') }}</span>
                <input v-model="editExpiresOn" class="text-input" type="date">
              </label>
            </div>
            <span class="field-label">{{ t('storageItem.location') }}</span>
            <LocationFilterBar v-model="editLocation" class="edit-location" :label="t('storageItem.location')" />
            <div class="edit-actions">
              <AppButton :disabled="saving || editQuantity <= 0 || !editStoredOn" @click="saveEdit">
                <AppIcon name="save" :size="18" />
                {{ saving ? t('storageItem.saving') : t('storageItem.save') }}
              </AppButton>
              <AppButton variant="ghost" :disabled="saving" @click="editOpen = false">{{ t('common.done') }}</AppButton>
            </div>
          </section>

          <div class="lot-actions">
            <AppButton variant="secondary" size="small" :disabled="!selectedLot" @click="openEdit">
              {{ t('storageItem.editLot') }}
            </AppButton>
            <AppButton
              variant="ghost"
              size="small"
              class="discard-action"
              :disabled="!selectedLot || discarding"
              @click="discardArmed ? confirmDiscard() : (discardArmed = true)"
            >
              {{ discarding ? t('storageItem.discarding') : discardArmed ? t('storageItem.confirmDiscard') : t('storageItem.discard') }}
            </AppButton>
          </div>
        </template>
      </details>

      <p v-if="errorMessage" class="inline-error" role="alert">{{ errorMessage }}</p>
    </main>

    <main v-else class="item-content">
      <section class="card gone-card">
        <h2>{{ t('storageItem.goneTitle') }}</h2>
        <p>{{ t('storageItem.goneBody', { location: t(`storage.scopes.${locationKey}`) }) }}</p>
        <AppButton @click="router.push('/')">{{ t('storageItem.backToStorage') }}</AppButton>
      </section>
    </main>

    <footer v-if="food && dirty" class="confirm-bar sheet-up">
      <span class="confirm-bar__summary">{{ t('storageItem.reviewChanges') }}</span>
      <div class="confirm-bar__actions">
        <AppButton variant="ghost" :disabled="applying" @click="resetDrafts">{{ t('storageItem.reset') }}</AppButton>
        <AppButton :disabled="applying || !formValid" @click="applyChanges">
          <AppIcon name="storage" :size="18" />
          {{ applying ? t('storageItem.updating') : t('storageItem.updateStorage') }}
        </AppButton>
      </div>
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
  font-size: var(--font-size-base);
}

/* ---- Identity hero ---- */

.hero-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.hero-card__identity {
  display: grid;
  min-width: 0;
  gap: var(--space-2);
}

.hero-card__name {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
}

.hero-card__badges {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.hero-card__urgency {
  display: inline-flex;
  align-items: center;
  gap: 4px;
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

/* ---- Direct inventory form ---- */

.inventory-form {
  display: grid;
  gap: var(--space-4);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-ink);
}

.section-title :deep(.app-icon) {
  color: var(--color-primary);
}

.inventory-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
}

.field-card {
  display: grid;
  min-width: 0;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
}

.field-card:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.field-card__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.field-card__label :deep(.app-icon) {
  color: var(--color-primary);
}

.field-card__input {
  min-height: 42px;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--color-ink);
  font-size: var(--font-size-lg);
  font-variant-numeric: tabular-nums;
  font-weight: var(--font-weight-semibold);
}

.field-card__input:focus-visible {
  outline: none;
}

/* ---- Lots disclosure ---- */

.lots-disclosure {
  padding: 0;
}

.lots-disclosure summary {
  display: flex;
  min-height: var(--tap-target-min);
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-radius: var(--radius-card);
  cursor: pointer;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  list-style: none;
}

.lots-disclosure summary::-webkit-details-marker {
  display: none;
}

.lots-disclosure__chevron {
  color: var(--color-muted);
  font-size: var(--font-size-lg);
  transition: transform var(--duration-base) var(--ease-standard);
}

.lots-disclosure[open] .lots-disclosure__chevron {
  transform: rotate(90deg);
}

.lots-disclosure > *:not(summary) {
  margin-right: var(--space-4);
  margin-left: var(--space-4);
}

.lots-disclosure > .lot-actions {
  padding-bottom: var(--space-4);
}

.lot-list {
  display: grid;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
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

.lot-actions {
  display: flex;
  gap: var(--space-2);
}

.lot-actions .discard-action {
  margin-left: auto;
  color: var(--color-danger-ink);
}

.lot-actions .discard-action:hover:not(:disabled) {
  background-color: var(--color-danger-soft);
}

.edit-section {
  margin-bottom: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
}

.edit-section h3 {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-base);
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

.edit-location {
  margin-bottom: var(--space-3);
}

.edit-actions {
  display: flex;
  gap: var(--space-2);
}

.edit-actions .app-button:first-child {
  flex: 1;
}

.inline-error {
  margin: var(--space-2) 0;
  color: var(--color-danger-ink);
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

/* ---- Confirm bar ---- */

.confirm-bar {
  position: fixed;
  z-index: var(--z-sticky);
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

.confirm-bar__summary {
  overflow: hidden;
  flex: 1;
  max-width: 320px;
  color: var(--color-muted);
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confirm-bar__actions {
  display: flex;
  gap: var(--space-2);
}

@media (max-width: 480px) {
  .inventory-form__grid {
    grid-template-columns: 1fr;
  }

  .confirm-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .confirm-bar__summary {
    max-width: none;
    text-align: center;
    white-space: normal;
  }

  .confirm-bar__actions > * {
    flex: 1;
  }
}
</style>
