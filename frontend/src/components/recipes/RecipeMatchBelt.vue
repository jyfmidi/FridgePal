<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { InventoryFood } from '../../features/storage/inventory'
import FoodToken from '../food-token/FoodToken.vue'

const props = defineProps<{ foods: InventoryFood[]; usedFoodKeys: string[] }>()
const { t } = useI18n()

const slots = computed(() =>
  Array.from({ length: 7 }, (_, index) => {
    const food = props.foods[index]
    return { food, used: food ? props.usedFoodKeys.includes(food.foodKey) : false }
  }),
)
</script>

<template>
  <div class="match-belt">
    <div
      v-for="({ food, used }, index) in slots"
      :key="food?.id ?? `empty-${index}`"
      class="match-belt__slot"
      :class="{ 'match-belt__slot--used': used }"
      role="img"
      :aria-label="food ? t(used ? 'recipeResults.used' : 'recipeResults.notUsed', { name: t(food.nameKey) }) : t('recipeResults.emptySlot', { position: index + 1 })"
    >
      <span class="match-belt__index" aria-hidden="true">{{ index + 1 }}</span>
      <span v-if="food" class="match-belt__food">
        <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="38" />
      </span>
      <span v-else class="match-belt__empty" aria-hidden="true">—</span>
    </div>
  </div>
</template>

<style scoped>
.match-belt {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  padding: var(--space-3) var(--space-2) var(--space-2);
  border-radius: var(--radius-card);
  background: var(--color-selection-tray);
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
}

.match-belt__slot {
  position: relative;
  display: grid;
  min-width: 0;
  min-height: 68px;
  place-items: center;
  border: 1px solid var(--color-selection-edge);
  border-radius: var(--radius-sm);
  color: var(--color-selection-muted);
  background: rgb(255 255 255 / 0.44);
  box-shadow: inset 0 1px 2px rgb(34 50 67 / 0.08);
  transition:
    background-color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard),
    opacity var(--duration-base) var(--ease-standard);
}

.match-belt__slot--used {
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-primary-soft), var(--shadow-sm);
}

.match-belt__index {
  position: absolute;
  z-index: 1;
  top: -9px;
  left: 50%;
  display: grid;
  width: 18px;
  height: 18px;
  place-items: center;
  transform: translateX(-50%);
  border: 1px solid var(--color-selection-edge);
  border-radius: var(--radius-full);
  color: var(--color-selection-muted);
  background: var(--color-surface);
  font-size: 0.625rem;
}

.match-belt__food {
  display: grid;
  place-items: center;
  opacity: 0.42;
  filter: grayscale(0.72) saturate(0.35);
}

.match-belt__slot--used .match-belt__food {
  opacity: 1;
  filter: none;
}

.match-belt__empty {
  color: var(--color-selection-muted);
  font-size: var(--font-size-base);
}

@media (max-width: 390px) {
  .match-belt {
    gap: 2px;
    padding-right: var(--space-1);
    padding-left: var(--space-1);
  }
}
</style>
