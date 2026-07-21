<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { StorageLocation } from '../features/storage/inventory'
import LocationIcon from './LocationIcon.vue'

withDefaults(defineProps<{ location: StorageLocation; compact?: boolean }>(), { compact: false })
const { t } = useI18n()
</script>

<template>
  <span class="location-badge" :class="[`location-badge--${location}`, { 'location-badge--compact': compact }]">
    <LocationIcon :location="location" :size="compact ? 12 : 14" />
    <span>{{ t(`storage.scopes.${location}`) }}</span>
  </span>
</template>

<style scoped>
.location-badge {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  gap: 4px;
  padding: 2px 7px 2px 5px;
  border: 1px solid;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  white-space: nowrap;
}

.location-badge--compact {
  min-height: 21px;
  gap: 3px;
  padding: 2px 6px 2px 4px;
  font-size: 0.625rem;
}

.location-badge--fridge {
  color: var(--color-location-fridge-ink);
  background: var(--color-location-fridge-bg);
  border-color: var(--color-location-fridge-edge);
}

.location-badge--freezer {
  color: var(--color-location-freezer-ink);
  background: var(--color-location-freezer-bg);
  border-color: var(--color-location-freezer-edge);
}

.location-badge--pantry {
  color: var(--color-location-pantry-ink);
  background: var(--color-location-pantry-bg);
  border-color: var(--color-location-pantry-edge);
}
</style>
