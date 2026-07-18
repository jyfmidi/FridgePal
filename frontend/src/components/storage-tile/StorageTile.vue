<script setup lang="ts">
import FoodToken from '../food-token/FoodToken.vue'
import type { InventoryFood } from '../../features/storage/inventory'

defineProps<{
  food: InventoryFood
  name: string
  quantityLabel: string
  urgencyLabel?: string
  compact?: boolean
}>()
</script>

<template>
  <button
    class="storage-tile"
    :class="[`storage-tile--${food.urgency}`, { 'storage-tile--compact': compact }]"
    type="button"
    :aria-label="`${name}, ${quantityLabel}${urgencyLabel ? `, ${urgencyLabel}` : ''}`"
  >
    <FoodToken :food-key="food.foodKey" :name="name" :size="compact ? 46 : 54" />
    <span class="storage-tile__name">{{ name }}</span>
    <span class="storage-tile__quantity">{{ quantityLabel }}</span>
    <span v-if="urgencyLabel" class="storage-tile__urgency">{{ urgencyLabel }}</span>
  </button>
</template>

<style scoped>
.storage-tile {
  display: flex;
  min-width: 0;
  min-height: 132px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: var(--space-2) var(--space-1);
  border-radius: var(--radius-lg);
  color: var(--color-urgency-neutral-ink);
  background: var(--color-urgency-neutral);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-neutral-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.4);
  transition: transform var(--duration-base) var(--ease-standard), box-shadow var(--duration-base) var(--ease-standard);
}

.storage-tile:hover {
  transform: translateY(-2px);
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-neutral-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.4);
}

.storage-tile--compact {
  min-height: 118px;
}

.storage-tile--past {
  color: var(--color-urgency-past-ink);
  background: var(--color-urgency-past);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-past-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.28);
}

.storage-tile--past:hover {
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-past-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.28);
}

.storage-tile--today {
  color: var(--color-urgency-today-ink);
  background: var(--color-urgency-today);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-today-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.3);
}

.storage-tile--today:hover {
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-today-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.3);
}

.storage-tile--soon {
  color: var(--color-urgency-soon-ink);
  background: var(--color-urgency-soon);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-soon-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.32);
}

.storage-tile--soon:hover {
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-soon-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.32);
}

.storage-tile--later {
  color: var(--color-urgency-later-ink);
  background: var(--color-urgency-later);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-later-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.35);
}

.storage-tile--later:hover {
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-later-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.35);
}

.storage-tile__name {
  display: -webkit-box;
  min-height: 2.3em;
  overflow: hidden;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  line-height: 1.15;
  text-align: center;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.storage-tile__quantity,
.storage-tile__urgency {
  font-size: var(--font-size-xs);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.storage-tile__urgency {
  margin-top: 2px;
  font-weight: var(--font-weight-medium);
}
</style>
