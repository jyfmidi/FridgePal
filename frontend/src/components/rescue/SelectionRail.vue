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
        v-if="food"
        type="button"
        class="selection-slot__food"
        :aria-label="t(editable ? 'rescue.removeFood' : 'rescue.selectedPosition', { name: t(food.nameKey), position: index + 1 })"
        @click="editable && emit('remove', food.id)"
      >
        <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="42" />
        <span>{{ t(food.nameKey) }}</span>
      </button>
      <button v-else type="button" class="selection-slot__empty" :aria-label="t('rescue.addAtPosition', { position: index + 1 })" @click="emit('add')">
        <span aria-hidden="true">＋</span>
      </button>
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
  background: var(--color-rail);
  background-image: var(--color-rail-gradient);
  box-shadow: var(--shadow-inset-rail);
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
  border: 1px solid var(--color-rail-edge);
  border-radius: var(--radius-full);
  color: var(--color-on-rail-muted);
  background: var(--color-rail);
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
  color: var(--color-on-rail);
  background: var(--color-rail-slot);
  box-shadow: inset 0 0 0 1px var(--color-rail-edge);
  transition:
    box-shadow var(--duration-base) var(--ease-standard),
    transform var(--duration-base) var(--ease-pop);
}

.selection-slot__food:hover {
  box-shadow: var(--shadow-token-active);
  transform: translateY(-1px);
}

.selection-slot__food span {
  width: 100%;
  overflow: hidden;
  font-size: 0.625rem;
  line-height: 1.1;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selection-slot__empty {
  border: 1px dashed var(--color-on-rail-muted);
  color: var(--color-on-rail-muted);
  background: transparent;
  box-shadow: none;
  font-size: 1.8rem;
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
