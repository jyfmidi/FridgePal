<script setup lang="ts">
withDefaults(defineProps<{
  variant?: 'page' | 'compact'
  label: string
}>(), {
  variant: 'compact',
})
</script>

<template>
  <div
    class="fridge-pal-loader"
    :class="`fridge-pal-loader--${variant}`"
    role="status"
    aria-live="polite"
    aria-atomic="true"
  >
    <img
      class="fridge-pal-loader__mark"
      src="/brand/fridge-pal-mark.svg"
      alt=""
      width="64"
      height="80"
    >
    <span class="fridge-pal-loader__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.fridge-pal-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  text-align: center;
}

.fridge-pal-loader--compact {
  gap: var(--space-2);
}

.fridge-pal-loader--page {
  gap: var(--space-3);
  min-height: min(52vh, 420px);
}

.fridge-pal-loader__mark {
  display: block;
  width: 48px;
  height: 60px;
}

.fridge-pal-loader--page .fridge-pal-loader__mark {
  width: 64px;
  height: 80px;
}

.fridge-pal-loader__label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-normal);
}

.fridge-pal-loader--page .fridge-pal-loader__label {
  font-size: var(--font-size-base);
}

@media (prefers-reduced-motion: no-preference) {
  .fridge-pal-loader__mark {
    animation: fridge-pal-wiggle-hop 1.65s var(--ease-standard) infinite;
    transform-origin: center bottom;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fridge-pal-loader__mark {
    animation: none;
  }
}

@keyframes fridge-pal-wiggle-hop {
  0%, 100% { transform: translateY(0) rotate(0deg) scale(1); }
  12% { transform: translateY(0) rotate(-4deg) scaleX(0.98); }
  24% { transform: translateY(0) rotate(4deg) scaleX(0.98); }
  36% { transform: translateY(2px) rotate(0deg) scale(1.04, 0.94); }
  52% { transform: translateY(-8px) rotate(0deg) scale(0.98, 1.03); }
  68% { transform: translateY(0) rotate(0deg) scale(1.04, 0.94); }
  80% { transform: translateY(-2px) rotate(0deg) scale(0.99, 1.01); }
}
</style>
