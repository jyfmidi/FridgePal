<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppChip from '../components/AppChip.vue'
import StorageTile from '../components/storage-tile/StorageTile.vue'
import type { InventoryFood, StorageLocation } from '../features/storage/inventory'
import { useInventoryStore } from '../features/storage/inventoryStore'

type Scope = 'all' | StorageLocation

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const scope = ref<Scope>('all')
const searchOpen = ref(false)
const searchQuery = ref('')
const { inventory, useSoonFoods, syncState, hydrateFromServer } = useInventoryStore()

onMounted(() => {
  void hydrateFromServer()
})

const scopes: Scope[] = ['all', 'fridge', 'freezer', 'pantry']

const visibleFoods = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase(locale.value)
  return inventory.value.filter((food) => {
    const inScope = scope.value === 'all' || food.location === scope.value
    const matches = !query || t(food.nameKey).toLocaleLowerCase(locale.value).includes(query)
    return inScope && matches
  })
})

function quantityLabel(food: InventoryFood): string {
  const value = new Intl.NumberFormat(locale.value, { maximumFractionDigits: 2 }).format(food.quantity)
  if (food.unit === 'piece') return value
  return `${value} ${t(`units.${food.unit}`, { count: food.quantity })}`
}

function urgencyLabel(food: InventoryFood): string | undefined {
  if (food.urgencyKey) return t(food.urgencyKey)
  if (!food.expiresOn) return undefined
  return new Intl.DateTimeFormat(locale.value, { month: 'short', day: 'numeric' }).format(new Date(`${food.expiresOn}T00:00:00`))
}

function toggleLocale() {
  locale.value = locale.value === 'en' ? 'zh-CN' : 'en'
  document.documentElement.lang = locale.value
}

/** UI-03 — a tile tap opens the ingredient detail/edit view. */
function openItem(food: InventoryFood) {
  void router.push({ path: '/storage/item', query: { food: food.foodKey, location: food.location.toUpperCase() } })
}
</script>

<template>
  <div class="storage-view">
    <header class="storage-header">
      <strong class="storage-header__brand">{{ t('app.title') }}</strong>
      <span class="storage-header__page">{{ t('storage.title') }}</span>
      <div class="storage-header__actions">
        <button class="icon-action" type="button" :aria-label="t('storage.search')" @click="searchOpen = !searchOpen">⌕</button>
        <button class="locale-action" type="button" @click="toggleLocale">{{ locale === 'en' ? '中文' : 'EN' }}</button>
        <AppButton class="add-action" @click="$router.push('/add-food')">{{ t('storage.addFood') }}</AppButton>
      </div>
    </header>

    <div v-if="searchOpen" class="storage-search">
      <label class="sr-only" for="storage-search">{{ t('storage.search') }}</label>
      <input id="storage-search" v-model="searchQuery" type="search" :placeholder="t('storage.searchPlaceholder')" autofocus>
    </div>

    <p v-if="route.query.sync === 'local' || syncState === 'local-only'" class="sync-notice">
      {{ t('storage.localOnly') }}
    </p>

    <section class="storage-section" aria-labelledby="use-soon-heading">
      <div class="section-heading">
        <div>
          <h1 id="use-soon-heading">{{ t('storage.useSoon') }}</h1>
          <p>{{ t('storage.needsAttention', { count: useSoonFoods.length }) }}</p>
        </div>
        <span class="section-heading__count">{{ useSoonFoods.length }}</span>
      </div>
      <div class="use-soon-grid stagger-in">
        <StorageTile
          v-for="food in useSoonFoods"
          :key="food.id"
          :food="food"
          :name="t(food.nameKey)"
          :quantity-label="quantityLabel(food)"
          :urgency-label="urgencyLabel(food)"
          @click="openItem(food)"
        />
      </div>
    </section>

    <section class="storage-section storage-section--inventory" aria-labelledby="inventory-heading">
      <div class="inventory-toolbar">
        <h2 id="inventory-heading" class="sr-only">{{ t('storage.inventory') }}</h2>
        <div class="scope-control" role="group" :aria-label="t('storage.locationFilter')">
          <AppChip v-for="item in scopes" :key="item" :selected="scope === item" @toggle="scope = item">
            {{ t(`storage.scopes.${item}`) }}
          </AppChip>
        </div>
        <span class="inventory-count">{{ t('storage.items', { count: visibleFoods.length }) }}</span>
      </div>

      <div v-if="visibleFoods.length" class="inventory-grid stagger-in">
        <StorageTile
          v-for="food in visibleFoods"
          :key="food.id"
          :food="food"
          :name="t(food.nameKey)"
          :quantity-label="quantityLabel(food)"
          compact
          @click="openItem(food)"
        />
      </div>
      <div v-else class="storage-empty">
        <p>{{ t('storage.noMatches') }}</p>
        <button type="button" @click="scope = 'all'; searchQuery = ''">{{ t('storage.clearFilters') }}</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.storage-view {
  width: min(100%, 1180px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
}

.storage-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-2);
  padding: var(--safe-area-top) var(--space-1) 0;
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.storage-header__brand,
.storage-header__page {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.storage-header__page {
  justify-self: center;
}

.storage-header__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
}

.icon-action,
.locale-action {
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
}

.icon-action {
  font-size: 1.6rem;
}

.locale-action {
  display: none;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.add-action {
  min-height: 40px;
  padding: var(--space-2) var(--space-3);
  white-space: nowrap;
}

.storage-search {
  padding: var(--space-3) 0 0;
}

.sync-notice {
  padding: var(--space-2) var(--space-3);
  margin-top: var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-urgency-soon-ink);
  background: var(--color-urgency-later);
  font-size: var(--font-size-xs);
}

.storage-search input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.storage-section {
  padding-top: var(--space-5);
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.section-heading h1 {
  font-size: var(--font-size-xl);
}

.section-heading p,
.inventory-count {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.section-heading__count {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: var(--radius-full);
  color: var(--color-urgency-soon-ink);
  background: var(--color-urgency-soon);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
}

.use-soon-grid,
.inventory-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.inventory-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.scope-control {
  display: grid;
  flex: 1;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-1);
  padding: 3px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-sunken);
}

.scope-control :deep(.app-chip) {
  min-width: 0;
  min-height: 36px;
  padding: var(--space-1);
  box-shadow: none;
}

.storage-empty {
  display: grid;
  min-height: 180px;
  place-items: center;
  align-content: center;
  gap: var(--space-2);
  border-radius: var(--radius-card);
  color: var(--color-muted);
  background: var(--color-surface);
}

.storage-empty button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 460px) {
  .storage-view {
    padding-right: var(--space-2);
    padding-left: var(--space-2);
  }

  .storage-header__brand,
  .storage-header__page {
    font-size: var(--font-size-base);
  }

  .add-action {
    font-size: var(--font-size-xs);
  }

  .inventory-count {
    display: none;
  }
}

@media (min-width: 720px) {
  .storage-view {
    padding-right: var(--space-6);
    padding-bottom: var(--space-10);
    padding-left: var(--space-6);
  }

  .locale-action {
    display: block;
  }

  .use-soon-grid {
    grid-template-columns: repeat(7, minmax(0, 1fr));
  }

  .inventory-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
</style>
