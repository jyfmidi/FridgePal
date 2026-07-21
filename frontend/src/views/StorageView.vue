<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppIcon from '../components/AppIcon.vue'
import AppPageHeader from '../components/AppPageHeader.vue'
import LocationFilterBar from '../components/LocationFilterBar.vue'
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
  const localized = ['g', 'kg', 'ml', 'l', 'piece'].includes(food.unit)
    ? t(`units.${food.unit}`, food.quantity)
    : food.unit
  return `${value} ${localized}`
}

function urgencyLabel(food: InventoryFood): string | undefined {
  if (food.urgencyKey) return t(food.urgencyKey)
  if (!food.expiresOn) return undefined
  return new Intl.DateTimeFormat(locale.value, { month: 'short', day: 'numeric' }).format(new Date(`${food.expiresOn}T00:00:00`))
}

/** UI-03 — a tile tap opens the ingredient detail/edit view. */
function openItem(food: InventoryFood) {
  void router.push({ path: '/storage/item', query: { food: food.foodKey, location: food.location.toUpperCase() } })
}
</script>

<template>
  <div class="storage-view">
    <AppPageHeader :title="t('storage.title')">
      <template #actions>
        <div class="storage-actions">
          <button class="icon-action" type="button" :aria-label="t('storage.search')" @click="searchOpen = !searchOpen">
            <AppIcon name="search" :size="20" />
          </button>
          <AppButton class="add-action" @click="$router.push('/add-food')">
            <AppIcon name="add" :size="18" />
            {{ t('storage.addFood') }}
          </AppButton>
        </div>
      </template>
    </AppPageHeader>

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
        <div class="inventory-toolbar__heading">
          <h2 id="inventory-heading">{{ t('storage.inventory') }}</h2>
          <span class="inventory-count">{{ t('storage.items', { count: visibleFoods.length }) }}</span>
        </div>
        <LocationFilterBar v-model="scope" include-all :label="t('storage.locationFilter')" />
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
        <img class="storage-empty__mark" src="/brand/fridge-pal-mark.svg" alt="" width="64" height="80">
        <p>{{ inventory.length === 0 ? t('storage.emptyAll') : t('storage.noMatches') }}</p>
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

.storage-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
}

.icon-action {
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  border-radius: var(--radius-sm);
  color: var(--color-primary);
  display: grid;
  place-items: center;
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
  color: var(--color-primary-hover);
  background: var(--color-primary-softer);
  box-shadow: inset 0 0 0 1px var(--color-primary-soft);
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
  color: var(--color-count-ink);
  background: var(--color-count-bg);
  box-shadow: inset 0 0 0 1px var(--color-count-edge);
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
  display: grid;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.inventory-toolbar__heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
}

.inventory-toolbar__heading h2 {
  font-size: var(--font-size-lg);
}

.inventory-count {
  flex: none;
  white-space: nowrap;
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

.storage-empty__mark {
  width: 64px;
  height: 80px;
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

  .add-action {
    font-size: var(--font-size-xs);
  }

}

@media (min-width: 720px) {
  .storage-view {
    padding-right: var(--space-6);
    padding-bottom: var(--space-10);
    padding-left: var(--space-6);
  }

  .use-soon-grid {
    grid-template-columns: repeat(7, minmax(0, 1fr));
  }

  .inventory-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
</style>
