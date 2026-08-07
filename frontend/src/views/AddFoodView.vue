<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import LocationFilterBar from '../components/LocationFilterBar.vue'
import {
  compatibleInventoryUnits,
  convertInventoryQuantity,
  inventoryUnits,
  isInventoryUnit,
  roundInventoryQuantity,
  type FoodCatalogItem,
  type InventoryUnit,
  type StorageLocation,
} from '../features/storage/inventory'
import { useFoodLibrary } from '../features/storage/libraryStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t, locale } = useI18n()
const router = useRouter()
const { inventory, checkIn } = useInventoryStore()
const { catalog, hydrateLibrary } = useFoodLibrary()

onMounted(() => {
  // The Food Library is admin-managed; merge server truth with the static
  // catalog so newly added preset foods appear in the typeahead.
  void hydrateLibrary()
})

const today = new Date().toISOString().slice(0, 10)
const query = ref('')

/** Draft for a food that is not in the built-in catalog (FR-LIB-003). */
interface CustomFoodDraft {
  custom: true
  name: string
  foodKey: string
}

const selected = ref<FoodCatalogItem | CustomFoodDraft | null>(null)
const location = ref<StorageLocation>('fridge')
const quantity = ref(1)
const unit = ref<InventoryUnit>('piece')
const storedOn = ref(today)
const expiresOn = ref('')
const saving = ref(false)

const trimmedQuery = computed(() => query.value.trim())

const selectedPresets = computed(() => {
  if (!selected.value || 'custom' in selected.value) return []
  return selected.value.packagePresets ?? []
})

function presetLabel(preset: NonNullable<FoodCatalogItem['packagePresets']>[number]): string {
  const activeLocale = locale.value as 'en' | 'zh-CN'
  return preset.label[activeLocale] ?? preset.label.en
}

/** Localized display name: catalog i18n key first, raw server names second. */
function displayName(food: FoodCatalogItem): string {
  const activeLocale = locale.value as 'en' | 'zh-CN'
  return food.nameKey ? t(food.nameKey) : (food.names[activeLocale] ?? food.names.en)
}

/** Typeahead match: localized name plus admin-managed aliases (both locales). */
function foodMatches(food: FoodCatalogItem, normalized: string): boolean {
  if (!normalized) return true
  const haystack = [
    displayName(food),
    food.names.en,
    food.names['zh-CN'],
    ...(food.aliases?.en ?? []),
    ...(food.aliases?.['zh-CN'] ?? []),
  ]
  return haystack.some((text) => text && text.toLocaleLowerCase(locale.value).includes(normalized))
}

const suggestions = computed(() => {
  const normalized = trimmedQuery.value.toLocaleLowerCase(locale.value)
  return catalog.value.filter((food) => foodMatches(food, normalized)).slice(0, 8)
})

const showCreateCustom = computed(() => trimmedQuery.value.length > 0 && suggestions.value.length === 0)
const isCustomSelected = computed(() => !!selected.value && 'custom' in selected.value)
const unitOptions = computed<InventoryUnit[]>(() => {
  if (isCustomSelected.value) return [...inventoryUnits]
  const selection = selected.value
  if (!selection || 'custom' in selection) return [...inventoryUnits]
  const existingUnit = inventory.value.find((food) => food.foodKey === selection.foodKey)?.unit
  const baseUnit = existingUnit && isInventoryUnit(existingUnit) ? existingUnit : selection.defaultUnit
  return compatibleInventoryUnits(baseUnit)
})

/** Lowercase, non-alphanumerics collapse to `-` (Unicode-aware so CJK names keep their characters). */
function slugify(name: string): string {
  return name.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '') || 'food'
}

const customFoodKey = computed(() => `custom:${slugify(trimmedQuery.value)}`)

function createCustomFood() {
  const name = trimmedQuery.value
  if (!name) return
  selected.value = { custom: true, name, foodKey: customFoodKey.value }
  unit.value = 'g'
  expiresOn.value = ''
}

function toDateInput(date: Date) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10)
}

function chooseFood(food: FoodCatalogItem) {
  selected.value = food
  location.value = food.defaultLocation
  const existingUnit = inventory.value.find((item) => item.foodKey === food.foodKey)?.unit
  if (existingUnit && isInventoryUnit(existingUnit)) {
    unit.value = existingUnit
    quantity.value = compatibleInventoryUnits(existingUnit).includes(food.defaultUnit)
      ? roundInventoryQuantity(
          convertInventoryQuantity(food.defaultQuantity, food.defaultUnit, existingUnit),
        )
      : 1
  } else {
    unit.value = food.defaultUnit
    quantity.value = food.defaultQuantity
  }
  if (food.shelfLifeDays !== undefined) {
    const suggested = new Date(`${storedOn.value}T00:00:00`)
    suggested.setDate(suggested.getDate() + food.shelfLifeDays)
    expiresOn.value = toDateInput(suggested)
  } else {
    expiresOn.value = ''
  }
}

function chooseUnit(event: Event) {
  const nextUnit = (event.target as HTMLSelectElement).value
  if (!isInventoryUnit(nextUnit) || nextUnit === unit.value) return
  try {
    quantity.value = roundInventoryQuantity(
      convertInventoryQuantity(quantity.value, unit.value, nextUnit),
    )
  } catch {
    // A new custom food may intentionally choose a different dimension.
  }
  unit.value = nextUnit
}

/** Quick-fill quantity and unit from an admin-managed package preset. */
function applyPreset(preset: NonNullable<FoodCatalogItem['packagePresets']>[number]) {
  unit.value = preset.unit
  quantity.value = preset.amount
}

async function save() {
  const selection = selected.value
  if (!selection || quantity.value <= 0) return
  saving.value = true
  const custom = 'custom' in selection
  const synced = await checkIn({
    foodKey: selection.foodKey,
    nameKey: custom ? undefined : selection.nameKey,
    names: custom ? { en: selection.name, 'zh-CN': selection.name } : selection.names,
    quantity: quantity.value,
    unit: unit.value,
    location: location.value,
    storedOn: storedOn.value,
    expiresOn: expiresOn.value || undefined,
  })
  if (custom && synced) {
    await hydrateLibrary(true)
  }
  await router.push({ path: '/', query: synced ? {} : { sync: 'local' } })
}
</script>

<template>
  <div class="add-food-view">
    <AppTaskHeader :title="t('addFood.title')" :back-label="t('common.back')" @back="router.back()" />

    <main class="add-food-content">
      <section>
        <label class="field-label" for="food-search">{{ t('addFood.chooseFood') }}</label>
        <input id="food-search" v-model="query" class="text-input" type="search" :placeholder="t('addFood.searchPlaceholder')">
        <div v-if="suggestions.length" class="suggestion-grid">
          <button
            v-for="food in suggestions"
            :key="food.foodKey"
            type="button"
            class="food-suggestion"
            :class="{ 'food-suggestion--selected': selected?.foodKey === food.foodKey }"
            :aria-label="displayName(food)"
            :aria-pressed="selected?.foodKey === food.foodKey"
            @click="chooseFood(food)"
          >
            <FoodToken :food-key="food.visualKey ?? food.foodKey" :name="displayName(food)" :size="50" />
            <span>{{ displayName(food) }}</span>
          </button>
        </div>
        <button
          v-if="showCreateCustom"
          type="button"
          class="create-custom"
          :class="{ 'create-custom--selected': isCustomSelected }"
          :aria-pressed="isCustomSelected"
          @click="createCustomFood"
        >
          <FoodToken :food-key="customFoodKey" :name="trimmedQuery" :size="50" />
          <span class="create-custom__text">
            <strong>{{ t('addFood.createNamed', { name: trimmedQuery }) }}</strong>
            <small>{{ t('addFood.createHint') }}</small>
          </span>
        </button>
      </section>

      <template v-if="selected">
        <section class="form-section">
          <span class="field-label">{{ t('addFood.location') }}</span>
          <LocationFilterBar v-model="location" :label="t('addFood.location')" />
        </section>

        <section class="form-section form-row">
          <label>
            <span class="field-label">{{ t('addFood.quantity') }}</span>
            <input v-model.number="quantity" class="text-input" type="number" min="0.01" step="0.01">
          </label>
          <label>
            <span class="field-label">{{ t(isCustomSelected ? 'addFood.baseUnit' : 'addFood.unit') }}</span>
            <select :value="unit" class="text-input" @change="chooseUnit">
              <option v-for="item in unitOptions" :key="item" :value="item">{{ t(`units.${item}`, quantity) }}</option>
            </select>
            <small v-if="isCustomSelected">{{ t('addFood.baseUnitHint') }}</small>
          </label>
        </section>

        <section v-if="selectedPresets.length" class="form-section">
          <span class="field-label">{{ t('addFood.presets') }}</span>
          <div class="preset-row">
            <button
              v-for="(preset, index) in selectedPresets"
              :key="index"
              type="button"
              class="preset-chip"
              :aria-label="t('addFood.applyPreset', { label: presetLabel(preset) })"
              @click="applyPreset(preset)"
            >
              {{ presetLabel(preset) }} · {{ preset.amount }} {{ t(`units.${preset.unit}`, preset.amount) }}
            </button>
          </div>
        </section>

        <section class="form-section form-row">
          <label>
            <span class="field-label">{{ t('addFood.storedOn') }}</span>
            <input v-model="storedOn" class="text-input" type="date">
          </label>
          <label>
            <span class="field-label">{{ t('addFood.expiresOn') }}</span>
            <input v-model="expiresOn" class="text-input" type="date">
            <small>{{ expiresOn ? t('addFood.librarySuggestion') : t('addFood.noExpiry') }}</small>
          </label>
        </section>
      </template>
    </main>

    <footer class="save-bar sheet-up">
      <AppButton block :disabled="!selected || quantity <= 0 || saving" @click="save">
        {{ saving ? t('addFood.saving') : t('addFood.save') }}
      </AppButton>
    </footer>
  </div>
</template>

<style scoped>
.add-food-view {
  width: min(100%, 720px);
  min-height: 100vh;
  padding-bottom: 92px;
  margin: 0 auto;
  background: var(--color-canvas);
}

.add-food-content {
  display: grid;
  gap: var(--space-6);
  padding: var(--space-5) var(--space-3);
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

.suggestion-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.food-suggestion {
  display: flex;
  min-width: 0;
  min-height: 104px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-align: center;
}

.food-suggestion--selected {
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
}

.create-custom {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border), var(--shadow-sm);
  text-align: left;
}

.create-custom--selected {
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
}

.create-custom__text {
  display: grid;
  gap: var(--space-1);
  font-size: var(--font-size-sm);
}

.create-custom__text small {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.form-section {
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.form-row small {
  display: block;
  margin-top: var(--space-1);
  color: var(--color-muted);
}

.preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.preset-chip {
  min-height: var(--tap-target-min);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-primary-soft);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  transition: background-color var(--duration-base) var(--ease-standard);
}

.preset-chip:hover {
  background: var(--color-primary-softer);
}

.save-bar {
  position: fixed;
  z-index: var(--z-sticky);
  right: 0;
  bottom: 0;
  left: 0;
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

@media (min-width: 880px) {
  .save-bar {
    left: 0;
  }
}
</style>
