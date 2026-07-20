<script setup lang="ts">
/**
 * Compact selectable chip (scope filters and package presets).
 * Renders as a toggle button with aria-pressed for assistive technology.
 */
withDefaults(
  defineProps<{
    selected?: boolean
    disabled?: boolean
  }>(),
  { selected: false, disabled: false },
)

defineEmits<{ toggle: [] }>()
</script>

<template>
  <button
    type="button"
    class="app-chip"
    :class="{ 'app-chip--selected': selected }"
    :aria-pressed="selected"
    :disabled="disabled"
    @click="$emit('toggle')"
  >
    <slot />
  </button>
</template>

<style scoped>
.app-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  min-height: var(--tap-target-min);
  padding: var(--space-1) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-tight);
  color: var(--color-ink-soft);
  background-color: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
  transition:
    background-color var(--duration-base) var(--ease-standard),
    color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard);
}

.app-chip:hover:not(:disabled):not(.app-chip--selected) {
  background-color: var(--color-surface-sunken);
}

.app-chip--selected {
  color: var(--color-on-primary);
  background-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.app-chip:disabled {
  opacity: 0.45;
}
</style>
