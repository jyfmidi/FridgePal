<script setup lang="ts">
import { useI18n } from 'vue-i18n'

defineProps<{ titleKey: string }>()
const { t } = useI18n()
</script>

<template>
  <section class="coming-soon">
    <p>{{ t('app.title') }}</p>
    <h1>{{ t(titleKey) }}</h1>
    <span>{{ t('common.comingNext') }}</span>
  </section>
</template>

<style scoped>
.coming-soon {
  display: grid;
  min-height: calc(100vh - 72px);
  place-items: center;
  align-content: center;
  gap: var(--space-2);
  padding: var(--space-6);
  text-align: center;
}

.coming-soon p,
.coming-soon span {
  color: var(--color-muted);
}
</style>
