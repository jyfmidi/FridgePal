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
    <svg
      class="fridge-pal-loader__mark"
      viewBox="0 0 64 80"
      aria-hidden="true"
      focusable="false"
    >
      <g class="fridge-pal-loader__character" data-motion="wiggle-hop">
        <g class="fridge-pal-loader__upper-door">
          <path fill="#F47B65" d="M12 4h40a6 6 0 0 1 6 6v26H6V10a6 6 0 0 1 6-6Z" />
        </g>
        <g class="fridge-pal-loader__lower-door">
          <path fill="#EE6A56" d="M6 40h52v30a6 6 0 0 1-6 6H12a6 6 0 0 1-6-6V40Z" />
        </g>
        <g class="fridge-pal-loader__eyes">
          <rect width="6" height="10" x="18" y="13" fill="#FFF" rx="1" />
          <rect width="6" height="10" x="34" y="13" fill="#FFF" rx="1" />
        </g>
        <g class="fridge-pal-loader__handles">
          <rect width="4" height="9" x="48" y="24" fill="#B84739" rx="2" />
          <rect width="4" height="14" x="48" y="45" fill="#B84739" rx="2" />
        </g>
      </g>
    </svg>
    <span class="fridge-pal-loader__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.fridge-pal-loader {
  display: grid;
  place-items: center;
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
  overflow: visible;
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

.fridge-pal-loader__character,
.fridge-pal-loader__upper-door,
.fridge-pal-loader__lower-door,
.fridge-pal-loader__eyes,
.fridge-pal-loader__handles {
  animation-name: none;
  transform-box: fill-box;
  transform-origin: center bottom;
}

@media (prefers-reduced-motion: no-preference) {
  .fridge-pal-loader__character {
    animation: fridge-pal-wiggle-hop 1.65s var(--ease-standard) infinite;
  }

  .fridge-pal-loader__upper-door,
  .fridge-pal-loader__eyes {
    animation: fridge-pal-upper-follow 1.65s var(--ease-standard) 35ms infinite;
  }

  .fridge-pal-loader__lower-door {
    animation: fridge-pal-lower-follow 1.65s var(--ease-standard) 20ms infinite;
  }

  .fridge-pal-loader__handles {
    animation: fridge-pal-handle-follow 1.65s var(--ease-standard) 55ms infinite;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fridge-pal-loader__character,
  .fridge-pal-loader__upper-door,
  .fridge-pal-loader__lower-door,
  .fridge-pal-loader__eyes,
  .fridge-pal-loader__handles {
    animation-name: none;
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

@keyframes fridge-pal-upper-follow {
  0%, 8%, 30%, 100% { transform: translateX(0) rotate(0deg); }
  16% { transform: translateX(0.35px) rotate(0.6deg); }
  28% { transform: translateX(-0.35px) rotate(-0.6deg); }
}

@keyframes fridge-pal-lower-follow {
  0%, 10%, 32%, 100% { transform: translateX(0) rotate(0deg); }
  18% { transform: translateX(0.2px) rotate(0.35deg); }
  30% { transform: translateX(-0.2px) rotate(-0.35deg); }
}

@keyframes fridge-pal-handle-follow {
  0%, 10%, 32%, 100% { transform: translateX(0); }
  18% { transform: translateX(0.5px); }
  30% { transform: translateX(-0.5px); }
}
</style>
