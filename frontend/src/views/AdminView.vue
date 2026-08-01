<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppPageHeader from '../components/AppPageHeader.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import LocationBadge from '../components/LocationBadge.vue'
import { deleteFoodDefinition, fetchAdminSettings, listFoodDefinitions, saveAdminSettings, type AdminSettings } from '../api/admin'
import type { LibraryFood } from '../api/library'
import { useFoodLibrary } from '../features/storage/libraryStore'

type AdminTab = 'foods' | 'settings'

const { t, locale } = useI18n()
const router = useRouter()
const { hydrateLibrary } = useFoodLibrary()

const tab = ref<AdminTab>('foods')
const foods = ref<LibraryFood[]>([])
const loading = ref(true)
const loadError = ref('')
const query = ref('')

// Settings tab state.
const settings = ref<AdminSettings>({ useSoonWindowDays: 5 })
const settingsSaving = ref(false)
const settingsMessage = ref('')
const settingsError = ref('')

async function loadFoods() {
  loading.value = true
  loadError.value = ''
  try {
    foods.value = await listFoodDefinitions()
    await hydrateLibrary(true)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('admin.errors.generic')
  } finally {
    loading.value = false
  }
}

async function loadSettings() {
  try {
    settings.value = await fetchAdminSettings()
  } catch (error) {
    settingsError.value = error instanceof Error ? error.message : t('admin.errors.generic')
  }
}

onMounted(() => {
  void loadFoods()
  void loadSettings()
})

const visibleFoods = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  return foods.value.filter((food) => {
    const haystack = `${food.names.en} ${food.names['zh-CN'] ?? ''} ${food.foodKey}`.toLocaleLowerCase(locale.value)
    return !normalized || haystack.includes(normalized)
  })
})

function displayName(food: LibraryFood): string {
  const activeLocale = locale.value as 'en' | 'zh-CN'
  return food.names[activeLocale] ?? food.names.en
}

function locationOf(food: LibraryFood): 'fridge' | 'freezer' | 'pantry' {
  return food.recommendedStorage.toLocaleLowerCase() as 'fridge' | 'freezer' | 'pantry'
}

function shelfLifeSummary(food: LibraryFood): string {
  if (!food.shelfLife.length) return t('admin.foods.noShelfLife')
  return food.shelfLife
    .map((rule) => `${t(`storage.scopes.${rule.storageLocation.toLocaleLowerCase()}`)} ${rule.durationDays}d`)
    .join(' · ')
}

function editFood(food: LibraryFood) {
  void router.push({ name: 'admin-food-edit', params: { foodKey: food.foodKey } })
}

async function removeFood(food: LibraryFood) {
  const confirmed = window.confirm(t('admin.foods.confirmDelete', { name: displayName(food) }))
  if (!confirmed) return
  try {
    await deleteFoodDefinition(food.foodKey)
    await loadFoods()
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('admin.errors.generic')
  }
}

async function saveSettings() {
  settingsSaving.value = true
  settingsMessage.value = ''
  settingsError.value = ''
  try {
    settings.value = await saveAdminSettings(settings.value)
    settingsMessage.value = t('admin.settings.saved')
  } catch (error) {
    settingsError.value = error instanceof Error ? error.message : t('admin.errors.generic')
  } finally {
    settingsSaving.value = false
  }
}
</script>

<template>
  <div class="admin-view">
    <AppPageHeader :title="t('admin.title')" />

    <main class="admin-content">
      <div class="admin-tabs" role="tablist" :aria-label="t('admin.tabsLabel')">
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'foods'"
          :class="{ 'admin-tabs__tab--selected': tab === 'foods' }"
          class="admin-tabs__tab"
          @click="tab = 'foods'"
        >
          {{ t('admin.tabs.foods') }}
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="tab === 'settings'"
          :class="{ 'admin-tabs__tab--selected': tab === 'settings' }"
          class="admin-tabs__tab"
          @click="tab = 'settings'"
        >
          {{ t('admin.tabs.settings') }}
        </button>
      </div>

      <section v-if="tab === 'foods'" class="admin-section">
        <div class="admin-toolbar">
          <label class="admin-search">
            <span class="sr-only">{{ t('admin.foods.search') }}</span>
            <input v-model="query" type="search" :placeholder="t('admin.foods.searchPlaceholder')">
          </label>
          <AppButton @click="router.push({ name: 'admin-food-new' })">
            {{ t('admin.foods.add') }}
          </AppButton>
        </div>

        <p v-if="loadError" class="admin-error" role="alert">{{ loadError }}</p>
        <p v-else-if="loading" class="admin-muted">{{ t('admin.foods.loading') }}</p>
        <p v-else-if="!visibleFoods.length" class="admin-muted">{{ t('admin.foods.empty') }}</p>

        <ul v-else class="admin-food-list">
          <li v-for="food in visibleFoods" :key="food.foodKey" class="admin-food-card" :class="{ 'admin-food-card--inactive': !food.active }">
            <FoodToken :food-key="food.foodKey" :name="displayName(food)" :size="48" />
            <div class="admin-food-card__copy">
              <strong>{{ displayName(food) }}</strong>
              <span class="admin-food-card__meta">
                <LocationBadge :location="locationOf(food)" />
                <span>{{ t(`units.${food.baseUnit}`, 1) }}</span>
                <span class="admin-food-card__category">{{ food.category }}</span>
                <span v-if="!food.active" class="admin-food-card__inactive">{{ t('admin.foods.inactive') }}</span>
              </span>
              <small>{{ food.names.en }} · {{ shelfLifeSummary(food) }}</small>
            </div>
            <div class="admin-food-card__actions">
              <AppButton size="small" variant="secondary" @click="editFood(food)">
                {{ t('admin.foods.edit') }}
              </AppButton>
              <AppButton size="small" variant="ghost" @click="removeFood(food)">
                {{ t('admin.foods.delete') }}
              </AppButton>
            </div>
          </li>
        </ul>
      </section>

      <section v-else class="admin-section">
        <form class="admin-settings-card" @submit.prevent="saveSettings">
          <h2>{{ t('admin.settings.title') }}</h2>
          <p class="admin-settings-card__hint">{{ t('admin.settings.useSoonHint') }}</p>
          <label class="admin-settings-field">
            <span class="field-label">{{ t('admin.settings.useSoonWindowDays') }}</span>
            <input
              v-model.number="settings.useSoonWindowDays"
              class="text-input"
              type="number"
              min="1"
              max="30"
              step="1"
            >
          </label>
          <p v-if="settingsError" class="admin-error" role="alert">{{ settingsError }}</p>
          <p v-if="settingsMessage" class="admin-success" role="status">{{ settingsMessage }}</p>
          <AppButton block type="submit" :disabled="settingsSaving || settings.useSoonWindowDays < 1">
            {{ settingsSaving ? t('admin.settings.saving') : t('admin.settings.save') }}
          </AppButton>
        </form>
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-view {
  width: min(100%, 940px);
  min-height: 100vh;
  padding: 0 var(--space-3) 96px;
  margin: 0 auto;
}

.admin-content {
  display: grid;
  gap: var(--space-4);
  padding-top: var(--space-4);
}

.admin-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-1);
  padding: 3px;
  border-radius: var(--radius-lg);
  background: var(--color-surface-sunken);
}

.admin-tabs__tab {
  min-height: var(--tap-target-min);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-muted);
}

.admin-tabs__tab--selected {
  color: var(--color-primary);
  background: var(--color-surface);
  border-color: var(--color-border);
  box-shadow: inset 0 0 0 1px var(--color-primary-soft), var(--shadow-sm);
}

.admin-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-2);
  align-items: center;
}

.admin-search input,
.text-input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.admin-food-list {
  display: grid;
  gap: var(--space-3);
}

.admin-food-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.admin-food-card--inactive {
  opacity: 0.65;
}

.admin-food-card__copy {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.admin-food-card__copy strong {
  font-size: var(--font-size-base);
}

.admin-food-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.admin-food-card__category {
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: var(--color-surface-sunken);
  font-weight: var(--font-weight-medium);
}

.admin-food-card__inactive {
  color: var(--color-danger);
  font-weight: var(--font-weight-semibold);
}

.admin-food-card__copy small {
  overflow: hidden;
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-food-card__actions {
  display: grid;
  gap: var(--space-1);
}

.admin-settings-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-5);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.admin-settings-card h2 {
  font-size: var(--font-size-lg);
}

.admin-settings-card__hint {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.admin-settings-field {
  display: grid;
  gap: var(--space-1);
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.admin-muted {
  padding: var(--space-6) 0;
  color: var(--color-muted);
  text-align: center;
}

.admin-error {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  background: var(--color-danger-soft);
  font-size: var(--font-size-sm);
}

.admin-success {
  color: var(--color-location-fridge-ink);
  font-size: var(--font-size-sm);
}

@media (max-width: 560px) {
  .admin-food-card {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .admin-food-card__actions {
    grid-column: 1 / -1;
    grid-template-columns: 1fr 1fr;
    padding-top: var(--space-1);
  }
}
</style>
