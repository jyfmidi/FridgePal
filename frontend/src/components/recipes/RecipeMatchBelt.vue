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
      :aria-label="food ? t(used ? 'recipeResults.used' : 'recipeResults.notUsed', { name: t(food.nameKey) }) : t('recipeResults.emptySlot', { position: index + 1 })"
    >
      <FoodToken v-if="food" :food-key="food.foodKey" :name="t(food.nameKey)" :size="34" />
      <span v-else aria-hidden="true">—</span>
    </div>
  </div>
</template>

<style scoped>
.match-belt {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-rail);
  background-image: var(--color-rail-gradient);
  box-shadow: var(--shadow-inset-rail);
}

.match-belt__slot {
  display: grid;
  min-width: 0;
  min-height: 52px;
  place-items: center;
  border-radius: var(--radius-sm);
  color: var(--color-on-rail-muted);
  background: rgb(8 18 38 / 0.72);
  opacity: 0.46;
  transition:
    background-color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard),
    opacity var(--duration-base) var(--ease-standard);
}

.match-belt__slot--used {
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  opacity: 1;
}
</style>
