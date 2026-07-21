<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { InventoryFood } from '../../features/storage/inventory'
import FoodToken from '../food-token/FoodToken.vue'

const props = defineProps<{ foods: InventoryFood[]; editable?: boolean }>()
const emit = defineEmits<{ add: []; remove: [foodId: string] }>()
const { t } = useI18n()

const slots = computed(() => Array.from({ length: 7 }, (_, index) => props.foods[index]))
</script>

<template>
  <div class="selection-rail" :aria-label="t('rescue.selectionLabel')">
    <div v-for="(food, index) in slots" :key="food?.id ?? `empty-${index}`" class="selection-slot">
      <span class="selection-slot__index" aria-hidden="true">{{ index + 1 }}</span>
      <button
        v-if="food && editable"
        type="button"
        class="selection-slot__food"
        :class="`selection-slot__food--${food.urgency}`"
        :aria-label="t('rescue.removeFood', { name: t(food.nameKey), position: index + 1 })"
        @click="emit('remove', food.id)"
      >
        <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="42" />
        <span>{{ t(food.nameKey) }}</span>
      </button>
      <div
        v-else-if="food"
        class="selection-slot__food selection-slot__food--static"
        :class="`selection-slot__food--${food.urgency}`"
        role="img"
        :aria-label="t('rescue.selectedPosition', { name: t(food.nameKey), position: index + 1 })"
      >
        <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="42" />
        <span>{{ t(food.nameKey) }}</span>
      </div>
      <button v-else-if="editable" type="button" class="selection-slot__empty" :aria-label="t('rescue.addAtPosition', { position: index + 1 })" @click="emit('add')">
        <span aria-hidden="true">＋</span>
      </button>
      <div v-else class="selection-slot__empty selection-slot__empty--static" role="img" :aria-label="t('recipeResults.emptySlot', { position: index + 1 })">
        <span aria-hidden="true">—</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.selection-rail {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  padding: var(--space-3) var(--space-2) var(--space-2);
  border-radius: var(--radius-card);
  background: var(--color-selection-tray);
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
}

.selection-slot {
  position: relative;
  min-width: 0;
}

.selection-slot__index {
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

.selection-slot__food,
.selection-slot__empty {
  display: flex;
  width: 100%;
  min-height: 82px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  background: var(--color-selection-slot);
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
  transition:
    box-shadow var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-pop);
}

.selection-slot__food--past {
  background: var(--color-urgency-past);
  box-shadow: inset 0 0 0 1px var(--color-urgency-past-edge);
}

.selection-slot__food--today {
  background: var(--color-urgency-today);
  box-shadow: inset 0 0 0 1px var(--color-urgency-today-edge);
}

.selection-slot__food--soon {
  background: var(--color-urgency-soon);
  box-shadow: inset 0 0 0 1px var(--color-urgency-soon-edge);
}

.selection-slot__food--later {
  background: var(--color-urgency-later);
  box-shadow: inset 0 0 0 1px var(--color-urgency-later-edge);
}

.selection-slot__food:hover {
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
  transform: translateY(-1px);
}

.selection-slot__food--static:hover {
  box-shadow: inset 0 0 0 1px var(--color-selection-edge);
  transform: none;
}

.selection-slot__food span {
  width: 100%;
  overflow: hidden;
  font-size: 0.625rem;
  line-height: 1.1;
  text-align: center;
  word-break: break-word;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.selection-slot__empty {
  border: 1px dashed var(--color-selection-muted);
  color: var(--color-selection-muted);
  background: rgb(255 255 255 / 0.42);
  box-shadow: none;
  font-size: 1.8rem;
}

.selection-slot__empty--static {
  border-style: solid;
  cursor: default;
  font-size: var(--font-size-base);
}

@media (max-width: 390px) {
  .selection-rail {
    gap: 2px;
    padding-right: var(--space-1);
    padding-left: var(--space-1);
  }

  .selection-slot__food,
  .selection-slot__empty {
    min-height: 76px;
  }
}
</style>
