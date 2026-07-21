<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppPageHeader from '../components/AppPageHeader.vue'
import FridgePalLoader from '../components/FridgePalLoader.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import { useRescueStore } from '../features/rescue/rescueStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t, locale } = useI18n()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedFoods, selectionCount, removeFood, performSearch, searching, clearSearch } = useRescueStore(inventory)
const cuisine = ref('')
const showSearchLoader = ref(false)
let searchLoaderTimer: ReturnType<typeof setTimeout> | undefined

const cuisineOptions = computed(() => [
  { value: '', label: t('rescue.cuisine.none') },
  { value: 'chinese', label: t('rescue.cuisine.chinese') },
  { value: 'japanese', label: t('rescue.cuisine.japanese') },
  { value: 'mediterranean', label: t('rescue.cuisine.mediterranean') },
  { value: 'american', label: t('rescue.cuisine.american') },
  { value: 'dessert', label: t('rescue.cuisine.dessert') },
])

onMounted(() => {
  void hydrateFromServer()
})

watch(searching, (isSearching) => {
  if (searchLoaderTimer !== undefined) {
    clearTimeout(searchLoaderTimer)
    searchLoaderTimer = undefined
  }
  if (!isSearching) {
    showSearchLoader.value = false
    return
  }
  searchLoaderTimer = setTimeout(() => {
    showSearchLoader.value = true
    searchLoaderTimer = undefined
  }, 150)
})

onBeforeUnmount(() => {
  if (searchLoaderTimer !== undefined) clearTimeout(searchLoaderTimer)
})

async function findIdeas() {
  clearSearch()
  await performSearch(locale.value, cuisine.value)
  void router.push('/rescue/results')
}
</script>

<template>
  <div class="rescue-view">
    <AppPageHeader :title="t('rescue.title')" />

    <main class="rescue-content" :class="{ 'rescue-content--loading': searching }">
      <section class="rescue-intro">
        <h1>{{ t('rescue.headline') }}</h1>
        <p>{{ t('rescue.subtitle') }}</p>
      </section>

      <SelectionRail :foods="selectedFoods" editable @add="router.push('/rescue/choose')" @remove="removeFood" />

      <div class="selection-summary">
        <strong>{{ t('rescue.selectedCount', { count: selectionCount }) }}</strong>
        <button type="button" @click="router.push('/rescue/choose')">{{ t('rescue.editFoods') }}</button>
      </div>

      <div class="cuisine-selector">
        <span class="cuisine-selector__label">{{ t('rescue.cuisine.label') }}</span>
        <div class="cuisine-chips">
          <button
            v-for="opt in cuisineOptions"
            :key="opt.value"
            type="button"
            class="cuisine-chip"
            :class="{ 'cuisine-chip--active': cuisine === opt.value }"
            :aria-pressed="cuisine === opt.value"
            @click="cuisine = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <AppButton block :disabled="selectionCount === 0 || searching" @click="findIdeas">
        {{ searching ? t('recipeResults.loading') : t('rescue.findIdeas') }}
      </AppButton>
    </main>

    <div v-if="showSearchLoader" class="rescue-loading-overlay">
      <div class="rescue-loading-overlay__inner">
        <FridgePalLoader variant="compact" :label="t('recipeResults.loading')" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.rescue-view {
  position: relative;
  width: min(100%, 760px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
}

.rescue-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  background: rgb(8 18 38 / 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.rescue-loading-overlay__inner {
  display: grid;
  gap: var(--space-4);
  justify-items: center;
  padding: var(--space-6);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-overlay);
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

.cuisine-selector {
  display: grid;
  gap: var(--space-2);
}

.cuisine-selector__label {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.cuisine-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.cuisine-chip {
  min-height: var(--tap-target-min);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--duration-base) var(--ease-standard);
}

.cuisine-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.cuisine-chip--active {
  border-color: var(--color-primary);
  color: var(--color-on-primary);
  background: var(--color-primary);
}
</style>
