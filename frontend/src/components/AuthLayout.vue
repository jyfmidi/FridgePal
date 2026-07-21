<script setup lang="ts">
/**
 * Shared layout for the login/register screens: cream canvas with a soft
 * coral glow, the brand mark (bounce-in entrance), product name + tagline,
 * and a white form card supplied via the default slot. Scrolls instead of
 * clipping on short viewports (B7).
 */
defineProps<{
  /** Localized tagline under the product name. */
  tagline: string
}>()
</script>

<template>
  <div class="auth-layout">
    <div class="auth-layout__inner">
      <header class="auth-layout__brand">
        <img class="auth-layout__mark" src="/brand/fridge-pal-mark.svg" alt="" width="96" height="96">
        <h1 class="auth-layout__name">Fridge Pal</h1>
        <p class="auth-layout__tagline">{{ tagline }}</p>
      </header>
      <div class="auth-layout__card">
        <slot />
      </div>
      <footer v-if="$slots.footer" class="auth-layout__footer">
        <slot name="footer" />
      </footer>
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background:
    radial-gradient(closest-side at 50% 0%, var(--color-brand-soft), transparent 75%),
    var(--color-canvas);
}

.auth-layout__inner {
  width: min(90%, 380px);
  margin: auto;
  display: grid;
  gap: var(--space-6);
  padding: var(--space-8) 0;
}

.auth-layout__brand {
  display: grid;
  justify-items: center;
  gap: var(--space-2);
  text-align: center;
}

.auth-layout__mark {
  width: 96px;
  height: 96px;
}

.auth-layout__name {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  letter-spacing: var(--letter-spacing-display);
  color: var(--color-brand-ink);
}

.auth-layout__tagline {
  font-size: var(--font-size-sm);
  color: var(--color-muted);
}

.auth-layout__card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-8);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
}

.auth-layout__footer {
  text-align: center;
}

@media (prefers-reduced-motion: no-preference) {
  .auth-layout__mark {
    animation: auth-mark-pop 480ms var(--ease-pop) both;
  }

  @keyframes auth-mark-pop {
    from {
      opacity: 0;
      transform: scale(0.6) translateY(12px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }
}
</style>
