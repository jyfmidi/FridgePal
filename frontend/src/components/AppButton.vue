<script setup lang="ts">
/**
 * Shared button primitive. Variants map to the semantic token layer:
 * primary (main action), secondary (quiet filled), ghost (text-only).
 */
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost'
    type?: 'button' | 'submit'
    disabled?: boolean
    /** Stretch to fill the container width. */
    block?: boolean
    /** Compact horizontal padding for card-level actions. */
    size?: 'default' | 'small'
  }>(),
  { variant: 'primary', type: 'button', disabled: false, block: false, size: 'default' },
)
</script>

<template>
  <button class="app-button" :class="[`app-button--${variant}`, `app-button--${size}`, { 'app-button--block': block }]" :type="type" :disabled="disabled">
    <slot />
  </button>
</template>

<style scoped>
.app-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  min-height: var(--tap-target-min);
  padding: var(--space-2) var(--space-5);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-tight);
  transition:
    background-color var(--duration-base) var(--ease-standard),
    box-shadow var(--duration-base) var(--ease-standard),
    color var(--duration-base) var(--ease-standard),
    transform var(--duration-fast) var(--ease-standard);
}

@media (prefers-reduced-motion: no-preference) {
  .app-button:active:not(:disabled) {
    transform: scale(0.97);
  }
}

.app-button:disabled {
  opacity: 0.45;
}

.app-button--block {
  width: 100%;
}

.app-button--small {
  padding-right: var(--space-3);
  padding-left: var(--space-3);
  font-size: var(--font-size-sm);
}

.app-button--primary {
  color: var(--color-on-primary);
  background-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.app-button--primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.app-button--secondary {
  color: var(--color-primary);
  background-color: var(--color-primary-soft);
}

.app-button--secondary:hover:not(:disabled) {
  background-color: var(--color-primary-softer);
  box-shadow: inset 0 0 0 1px var(--color-primary-soft);
}

.app-button--ghost {
  color: var(--color-primary);
  background-color: transparent;
}

.app-button--ghost:hover:not(:disabled) {
  background-color: var(--color-primary-softer);
}
</style>
