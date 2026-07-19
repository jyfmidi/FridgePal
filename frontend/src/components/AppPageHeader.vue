<script setup lang="ts">
import { useI18n } from 'vue-i18n'

defineProps<{ title: string }>()
const { t } = useI18n()
</script>

<template>
  <header class="app-page-header">
    <img
      class="app-page-header__brand"
      src="/brand/fridge-pal-mark.svg"
      :alt="t('app.title')"
      width="32"
      height="40"
    >
    <h1 class="app-page-header__title">{{ title }}</h1>
    <div class="app-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.app-page-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: minmax(72px, 1fr) auto minmax(72px, 1fr);
  align-items: center;
  gap: var(--space-2);
  padding: var(--safe-area-top) var(--space-1) 0;
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.app-page-header__brand {
  display: block;
  width: 32px;
  height: 40px;
  object-fit: contain;
}

.app-page-header__title {
  justify-self: center;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--letter-spacing-tight);
}

.app-page-header__actions {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
}

@media (min-width: 720px) {
  .app-page-header__title {
    font-size: var(--font-size-lg);
  }

  .app-page-header__brand {
    width: 34px;
    height: 44px;
  }
}
</style>
