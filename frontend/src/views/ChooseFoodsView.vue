<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppChip from '../components/AppChip.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import { useRescueStore } from '../features/rescue/rescueStore'
import type { InventoryFood, StorageLocation } from '../features/storage/inventory'
import { useInventoryStore } from '../features/storage/inventoryStore'

type Scope = 'all' | StorageLocation

const { t, locale } = useI18n()
const router = useRouter()
const scope = ref<Scope>('all')
const query = ref('')
const scopes: Scope[] = ['all', 'fridge', 'freezer', 'pantry']
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedIds, selectedFoods, isAtCapacity, toggleFood, removeFood } = useRescueStore(inventory)

onMounted(() => {
  void hydrateFromServer()
})

const visibleFoods = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  return inventory.value.filter((food) => {
    const inScope = scope.value === 'all' || food.location === scope.value
    return inScope && (!normalized || t(food.nameKey).toLocaleLowerCase(locale.value).includes(normalized))
  })
})

function isSelected(food: InventoryFood) {
  return selectedIds.value.includes(food.id)
}
</script>

<template>
  <div class="choose-foods-view">
    <header class="picker-header">
      <button type="button" :aria-label="t('common.back')" @click="router.back()">‹</button>
      <h1>{{ t('rescue.chooseFoods') }}</h1>
      <button type="button" @click="router.push('/rescue')">{{ t('common.done') }}</button>
    </header>

    <main class="picker-content">
      <SelectionRail :foods="selectedFoods" editable @remove="removeFood" />
      <strong class="picker-count">{{ t('rescue.ofSeven', { count: selectedIds.length }) }}</strong>

      <div class="picker-toolbar">
        <div class="picker-scopes">
          <AppChip v-for="item in scopes" :key="item" :selected="scope === item" @toggle="scope = item">
            {{ t(`storage.scopes.${item}`) }}
          </AppChip>
        </div>
        <label>
          <span class="sr-only">{{ t('storage.search') }}</span>
          <input v-model="query" type="search" :placeholder="t('storage.searchPlaceholder')">
        </label>
      </div>

      <div class="food-picker-grid stagger-in">
        <button
          v-for="food in visibleFoods"
          :key="food.id"
          type="button"
          class="food-picker-tile"
          :class="{ 'food-picker-tile--selected': isSelected(food) }"
          :disabled="isAtCapacity && !isSelected(food)"
          :aria-pressed="isSelected(food)"
          :aria-label="t(food.nameKey)"
          @click="toggleFood(food.id)"
        >
          <span v-if="isSelected(food)" class="food-picker-tile__check" aria-hidden="true">✓</span>
          <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="54" />
          <span>{{ t(food.nameKey) }}</span>
        </button>
      </div>
    </main>

    <footer class="picker-footer sheet-up">
      <button type="button" @click="router.push('/rescue')">
        {{ t('rescue.doneFoods', { count: selectedIds.length }) }}
      </button>
    </footer>
  </div>
</template>

<style scoped>
.choose-foods-view {
  width: min(100%, 920px);
  min-height: 100vh;
  padding-bottom: 88px;
  margin: 0 auto;
}

.picker-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: 72px 1fr 72px;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  text-align: center;
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
}

.picker-header h1 {
  font-size: var(--font-size-lg);
}

.picker-header button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.picker-header button:first-child {
  justify-self: start;
  font-size: 2rem;
}

.picker-content {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-3);
}

.picker-count {
  text-align: center;
}

.picker-toolbar {
  display: grid;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.picker-scopes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-1);
}

.picker-toolbar input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.food-picker-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.food-picker-tile {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 126px;
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
  transition: transform var(--duration-base) var(--ease-pop), box-shadow var(--duration-base) var(--ease-standard);
}

.food-picker-tile--selected {
  background: var(--color-primary-softer);
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-token-active);
}

.food-picker-tile:disabled {
  opacity: 0.45;
}

.food-picker-tile__check {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: var(--radius-full);
  color: var(--color-on-primary);
  background: var(--color-primary);
}

.picker-footer {
  position: fixed;
  z-index: var(--z-sticky);
  right: 0;
  bottom: 0;
  left: 0;
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

.picker-footer button {
  width: 100%;
  min-height: 52px;
  border-radius: var(--radius-lg);
  color: var(--color-on-primary);
  background: var(--color-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

@media (min-width: 720px) {
  .picker-toolbar {
    grid-template-columns: 1fr 280px;
  }

  .food-picker-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
</style>
