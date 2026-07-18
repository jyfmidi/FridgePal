<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppChip from '../components/AppChip.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { foodCatalog, type FoodCatalogItem, type InventoryUnit, type StorageLocation } from '../features/storage/inventory'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t, locale } = useI18n()
const router = useRouter()
const { checkIn } = useInventoryStore()

const today = new Date().toISOString().slice(0, 10)
const query = ref('')
const selected = ref<FoodCatalogItem | null>(null)
const location = ref<StorageLocation>('fridge')
const quantity = ref(1)
const unit = ref<InventoryUnit>('piece')
const storedOn = ref(today)
const expiresOn = ref('')
const saving = ref(false)

const locations: StorageLocation[] = ['fridge', 'freezer', 'pantry']
const units: InventoryUnit[] = ['g', 'kg', 'ml', 'piece', 'head', 'bulb']

const suggestions = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  return foodCatalog.filter((food) => !normalized || t(food.nameKey).toLocaleLowerCase(locale.value).includes(normalized)).slice(0, 8)
})

function toDateInput(date: Date) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 10)
}

function chooseFood(food: FoodCatalogItem) {
  selected.value = food
  location.value = food.defaultLocation
  quantity.value = food.defaultQuantity
  unit.value = food.defaultUnit
  if (food.shelfLifeDays !== undefined) {
    const suggested = new Date(`${storedOn.value}T00:00:00`)
    suggested.setDate(suggested.getDate() + food.shelfLifeDays)
    expiresOn.value = toDateInput(suggested)
  } else {
    expiresOn.value = ''
  }
}

async function save() {
  if (!selected.value || quantity.value <= 0) return
  saving.value = true
  const synced = await checkIn({
    foodKey: selected.value.foodKey,
    nameKey: selected.value.nameKey,
    names: selected.value.names,
    quantity: quantity.value,
    unit: unit.value,
    location: location.value,
    storedOn: storedOn.value,
    expiresOn: expiresOn.value || undefined,
  })
  await router.push({ path: '/', query: synced ? {} : { sync: 'local' } })
}
</script>

<template>
  <div class="add-food-view">
    <header class="task-header">
      <button type="button" :aria-label="t('common.back')" @click="router.back()">‹</button>
      <h1>{{ t('addFood.title') }}</h1>
      <span aria-hidden="true" />
    </header>

    <main class="add-food-content">
      <section>
        <label class="field-label" for="food-search">{{ t('addFood.chooseFood') }}</label>
        <input id="food-search" v-model="query" class="text-input" type="search" :placeholder="t('addFood.searchPlaceholder')">
        <div class="suggestion-grid">
          <button
            v-for="food in suggestions"
            :key="food.foodKey"
            type="button"
            class="food-suggestion"
            :class="{ 'food-suggestion--selected': selected?.foodKey === food.foodKey }"
            :aria-label="t(food.nameKey)"
            :aria-pressed="selected?.foodKey === food.foodKey"
            @click="chooseFood(food)"
          >
            <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="50" />
            <span>{{ t(food.nameKey) }}</span>
          </button>
        </div>
      </section>

      <template v-if="selected">
        <section class="form-section">
          <span class="field-label">{{ t('addFood.location') }}</span>
          <div class="segmented-control">
            <AppChip v-for="item in locations" :key="item" :selected="location === item" @toggle="location = item">
              {{ t(`storage.scopes.${item}`) }}
            </AppChip>
          </div>
        </section>

        <section class="form-section form-row">
          <label>
            <span class="field-label">{{ t('addFood.quantity') }}</span>
            <input v-model.number="quantity" class="text-input" type="number" min="0.01" step="0.01">
          </label>
          <label>
            <span class="field-label">{{ t('addFood.unit') }}</span>
            <select v-model="unit" class="text-input">
              <option v-for="item in units" :key="item" :value="item">{{ t(`units.${item}`, { count: quantity }) }}</option>
            </select>
          </label>
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

.task-header button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-size: 2rem;
}

.task-header h1 {
  font-size: var(--font-size-lg);
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

.form-section {
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.segmented-control {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-1);
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
