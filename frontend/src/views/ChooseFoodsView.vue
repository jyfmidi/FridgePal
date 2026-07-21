<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import LocationFilterBar from '../components/LocationFilterBar.vue'
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
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedIds, selectedFoods, selectionCount, isAtCapacity, toggleFood, removeFood } = useRescueStore(inventory)

onMounted(() => {
  void hydrateFromServer()
})

const urgencyRank: Record<string, number> = {
  past: 5,
  today: 4,
  soon: 3,
  later: 2,
  neutral: 1,
}

const visibleFoods = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  return inventory.value
    .filter((food) => {
      const inScope = scope.value === 'all' || food.location === scope.value
      return inScope && (!normalized || t(food.nameKey).toLocaleLowerCase(locale.value).includes(normalized))
    })
    .sort((a, b) => (urgencyRank[b.urgency] ?? 0) - (urgencyRank[a.urgency] ?? 0))
})

function isSelected(food: InventoryFood) {
  return selectedIds.value.includes(food.id)
}
</script>

<template>
  <div class="choose-foods-view">
    <AppTaskHeader :title="t('rescue.chooseFoods')" :back-label="t('common.back')" @back="router.back()">
      <template #action>
        <button type="button" @click="router.push('/rescue')">{{ t('common.done') }}</button>
      </template>
    </AppTaskHeader>

    <main class="picker-content">
      <SelectionRail :foods="selectedFoods" editable @remove="removeFood" />
      <strong class="picker-count">{{ t('rescue.ofSeven', { count: selectionCount }) }}</strong>

      <div class="picker-toolbar">
        <LocationFilterBar v-model="scope" include-all :label="t('storage.locationFilter')" />
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
          :class="[
            `food-picker-tile--${food.urgency}`,
            { 'food-picker-tile--selected': isSelected(food) },
          ]"
          :disabled="isAtCapacity && !isSelected(food)"
          :aria-pressed="isSelected(food)"
          :aria-label="t(food.nameKey)"
          @click="toggleFood(food.id)"
        >
          <span v-if="isSelected(food)" class="food-picker-tile__check" aria-hidden="true">✓</span>
          <span v-if="food.urgencyKey" class="food-picker-tile__urgency" aria-hidden="true">{{ t(food.urgencyKey) }}</span>
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
  background: var(--color-urgency-neutral);
  box-shadow: inset 0 0 0 1px var(--color-urgency-neutral-edge);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-align: center;
  transition: transform var(--duration-base) var(--ease-pop), box-shadow var(--duration-base) var(--ease-standard);
}

.food-picker-tile--past {
  background: var(--color-urgency-past);
  box-shadow: inset 0 0 0 1px var(--color-urgency-past-edge);
}

.food-picker-tile--today {
  background: var(--color-urgency-today);
  box-shadow: inset 0 0 0 1px var(--color-urgency-today-edge);
}

.food-picker-tile--soon {
  background: var(--color-urgency-soon);
  box-shadow: inset 0 0 0 1px var(--color-urgency-soon-edge);
}

.food-picker-tile--later {
  background: var(--color-urgency-later);
  box-shadow: inset 0 0 0 1px var(--color-urgency-later-edge);
}

.food-picker-tile--selected {
  box-shadow: inset 0 0 0 3px var(--color-primary), var(--shadow-token-active);
}

.food-picker-tile:disabled {
  opacity: 0.45;
}

.food-picker-tile__urgency {
  position: absolute;
  top: var(--space-1);
  left: var(--space-1);
  padding: 1px var(--space-1);
  border-radius: var(--radius-full);
  background: rgb(255 255 255 / 0.6);
  font-size: 9px;
  font-weight: var(--font-weight-bold);
  line-height: 1.3;
  white-space: nowrap;
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
