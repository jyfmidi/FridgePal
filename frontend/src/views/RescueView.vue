<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import { useRescueStore } from '../features/rescue/rescueStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t } = useI18n()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedFoods, selectedIds, removeFood } = useRescueStore(inventory)

onMounted(() => {
  void hydrateFromServer()
})
</script>

<template>
  <div class="rescue-view">
    <header class="rescue-header">
      <strong>{{ t('app.title') }}</strong>
      <span>{{ t('rescue.title') }}</span>
      <button type="button">{{ t('rescue.recent') }}</button>
    </header>

    <main class="rescue-content">
      <section class="rescue-intro">
        <h1>{{ t('rescue.headline') }}</h1>
        <p>{{ t('rescue.subtitle') }}</p>
      </section>

      <SelectionRail :foods="selectedFoods" editable @add="router.push('/rescue/choose')" @remove="removeFood" />

      <div class="selection-summary">
        <strong>{{ t('rescue.selectedCount', { count: selectedIds.length }) }}</strong>
        <button type="button" @click="router.push('/rescue/choose')">{{ t('rescue.editFoods') }}</button>
      </div>

      <AppButton block :disabled="selectedIds.length === 0" @click="router.push('/rescue/results')">
        {{ t('rescue.findIdeas') }}
      </AppButton>

      <section class="recent-searches">
        <h2>{{ t('rescue.continueTitle') }}</h2>
        <div class="recent-card-row">
          <article>
            <strong>{{ t('rescue.recentHighProtein') }}</strong>
            <span>{{ t('rescue.foodCount', { count: 5 }) }}</span>
          </article>
          <article>
            <strong>{{ t('rescue.recentFresh') }}</strong>
            <span>{{ t('rescue.foodCount', { count: 7 }) }}</span>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.rescue-view {
  width: min(100%, 760px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
}

.rescue-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.rescue-header strong,
.rescue-header span {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.rescue-header button {
  min-height: var(--tap-target-min);
  justify-self: end;
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.rescue-content {
  display: grid;
  gap: var(--space-5);
  padding-top: var(--space-6);
}

.rescue-intro h1 {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  letter-spacing: var(--letter-spacing-display);
  line-height: var(--line-height-tight);
}

.rescue-intro p {
  margin-top: var(--space-1);
  color: var(--color-muted);
}

.selection-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.selection-summary button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.recent-searches {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.recent-searches h2 {
  margin-bottom: var(--space-3);
  font-size: var(--font-size-lg);
}

.recent-card-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.recent-card-row article {
  display: flex;
  min-height: 92px;
  flex-direction: column;
  justify-content: end;
  gap: var(--space-1);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.recent-card-row span {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}
</style>
