<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import AppIcon from '../AppIcon.vue'
import FoodToken from '../food-token/FoodToken.vue'
import LocationBadge from '../LocationBadge.vue'
import type { InventoryFood } from '../../features/storage/inventory'

const props = defineProps<{
  food: InventoryFood
  name: string
  quantityLabel: string
  urgencyLabel?: string
  compact?: boolean
}>()

const { t } = useI18n()

const locationLabel = computed(() => t(`storage.scopes.${props.food.location}`))
const ariaLabel = computed(
  () =>
    `${props.name}, ${props.quantityLabel}${props.urgencyLabel ? `, ${props.urgencyLabel}` : ''}, ${locationLabel.value}`,
)
const urgencyIcon = computed<'clock' | 'tombstone'>(() => (props.food.urgency === 'past' ? 'tombstone' : 'clock'))
</script>

<template>
  <button
    class="storage-tile"
    :class="[`storage-tile--${food.urgency}`, { 'storage-tile--compact': compact }]"
    type="button"
    :aria-label="ariaLabel"
  >
    <LocationBadge class="storage-tile__location" :location="food.location" compact />
    <FoodToken :food-key="food.foodKey" :name="name" :size="compact ? 46 : 54" />
    <span class="storage-tile__name">{{ name }}</span>
    <span class="storage-tile__quantity">
      <strong>{{ quantityLabel }}</strong>
    </span>
    <span v-if="urgencyLabel" class="storage-tile__urgency">
      <AppIcon :name="urgencyIcon" :size="15" />
      {{ urgencyLabel }}
    </span>
  </button>
</template>

<style scoped>
.storage-tile {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 154px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 30px var(--space-1) var(--space-2);
  border-radius: var(--radius-lg);
  color: var(--color-urgency-neutral-ink);
  background: var(--color-urgency-neutral);
  box-shadow:
    inset 0 0 0 1px var(--color-urgency-neutral-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.4);
  transition: transform var(--duration-fast) var(--ease-standard), box-shadow var(--duration-base) var(--ease-standard);
}

@media (prefers-reduced-motion: no-preference) {
  .storage-tile:active {
    transform: scale(0.97);
  }
}

.storage-tile:hover {
  transform: translateY(-2px);
  box-shadow:
    var(--shadow-md),
    inset 0 0 0 1px var(--color-urgency-neutral-edge),
    inset 0 1px 0 rgb(255 255 255 / 0.4);
}

.storage-tile--compact {
  min-height: 132px;
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

.storage-tile__location {
  position: absolute;
  top: 7px;
  left: 7px;
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
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.storage-tile__quantity {
  max-width: calc(100% - var(--space-2));
  padding: 3px 5px;
  border: 1px solid rgb(43 57 45 / 0.12);
  border-radius: var(--radius-full);
  background: rgb(255 255 255 / 0.58);
  white-space: nowrap;
}

.storage-tile__quantity strong {
  overflow: hidden;
  text-overflow: ellipsis;
}

.storage-tile__urgency {
  margin-top: 3px;
  font-weight: var(--font-weight-semibold);
}
</style>
