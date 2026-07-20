<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { StorageLocation } from '../features/storage/inventory'
import AppIcon from './AppIcon.vue'
import LocationIcon from './LocationIcon.vue'

export type LocationScope = 'all' | StorageLocation

const props = withDefaults(
  defineProps<{
    modelValue: LocationScope
    includeAll?: boolean
    label: string
  }>(),
  { includeAll: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: LocationScope] }>()
const { t } = useI18n()
const locations: StorageLocation[] = ['fridge', 'freezer', 'pantry']
const options: LocationScope[] = props.includeAll ? ['all', ...locations] : locations
</script>

<template>
  <div class="location-filter" :class="{ 'location-filter--with-all': includeAll }" role="group" :aria-label="label">
    <button
      v-for="item in options"
      :key="item"
      type="button"
      class="location-filter__option"
      :class="[`location-filter__option--${item}`, { 'location-filter__option--selected': modelValue === item }]"
      :aria-pressed="modelValue === item"
      @click="emit('update:modelValue', item)"
    >
      <AppIcon v-if="item === 'all'" name="grid" :size="17" />
      <LocationIcon v-else :location="item" :size="17" />
      <span>{{ t(`storage.scopes.${item}`) }}</span>
    </button>
  </div>
</template>

<style scoped>
.location-filter {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-1);
  width: 100%;
  padding: 3px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-sunken);
}

.location-filter--with-all {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.location-filter__option {
  display: inline-flex;
  min-width: 0;
  min-height: var(--tap-target-min);
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: var(--space-1) 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  transition: transform var(--duration-fast) var(--ease-standard), box-shadow var(--duration-base) var(--ease-standard);
}

.location-filter__option:hover {
  transform: translateY(-1px);
}

.location-filter__option--all {
  color: var(--color-primary);
  background: var(--color-surface);
  border-color: var(--color-border);
}

.location-filter__option--fridge {
  color: var(--color-location-fridge-ink);
  background: var(--color-location-fridge-bg);
  border-color: var(--color-location-fridge-edge);
}

.location-filter__option--freezer {
  color: var(--color-location-freezer-ink);
  background: var(--color-location-freezer-bg);
  border-color: var(--color-location-freezer-edge);
}

.location-filter__option--pantry {
  color: var(--color-location-pantry-ink);
  background: var(--color-location-pantry-bg);
  border-color: var(--color-location-pantry-edge);
}

.location-filter__option--selected {
  box-shadow: inset 0 0 0 2px currentColor, var(--shadow-sm);
}

.location-filter__option:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

@media (max-width: 390px) {
  .location-filter__option {
    gap: 3px;
    padding-right: 3px;
    padding-left: 3px;
    font-size: 0.6875rem;
  }
}
</style>
