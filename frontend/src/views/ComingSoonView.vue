<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppPageHeader from '../components/AppPageHeader.vue'

defineProps<{ titleKey: string }>()
const { t } = useI18n()
</script>

<template>
  <div class="coming-soon-view">
    <AppPageHeader :title="t(titleKey)" />
    <section class="coming-soon">
      <h2>{{ t(titleKey) }}</h2>
      <span>{{ t('common.comingNext') }}</span>
    </section>
  </div>
</template>

<style scoped>
.coming-soon-view {
  width: min(100%, 940px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
}

.coming-soon {
  display: grid;
  min-height: calc(100vh - 72px);
  place-items: center;
  align-content: center;
  gap: var(--space-2);
  padding: var(--space-6);
  text-align: center;
}

.coming-soon span {
  color: var(--color-muted);
}
</style>
