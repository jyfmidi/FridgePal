<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppPageHeader from '../components/AppPageHeader.vue'
import AppButton from '../components/AppButton.vue'
import AppIcon, { type AppIconName } from '../components/AppIcon.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { fetchHistory, undoEvent, type HistoryEvent } from '../api/history'
import { fetchMealIdeaHistory, type RescueSession } from '../api/rescue'
import { useInventoryStore } from '../features/storage/inventoryStore'
import { useRescueStore } from '../features/rescue/rescueStore'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const inventoryStore = useInventoryStore()
const { newMealIdea, clearNewMealIdea } = useRescueStore(inventoryStore.inventory)

const activeTab = ref<'storage' | 'meal-ideas'>('storage')

const events = ref<HistoryEvent[]>([])
const mealIdeas = ref<RescueSession[]>([])
const loading = ref(false)
const mealIdeasLoading = ref(false)
const error = ref<string | null>(null)
const undoingEventId = ref<string | null>(null)

const eventIconMap = {
  CHECK_IN: 'stock-in',
  EDIT: 'edit',
  MOVE: 'move',
  MANUAL_CONSUMPTION: 'consume',
  COOKING: 'cooking-pot',
  DISCARD: 'trash',
  REVERSAL: 'undo',
} satisfies Record<HistoryEvent['eventType'], AppIconName>

async function loadHistory() {
  loading.value = true
  error.value = null
  try {
    events.value = await fetchHistory()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadMealIdeas() {
  mealIdeasLoading.value = true
  try {
    mealIdeas.value = await fetchMealIdeaHistory(3)
  } catch {
    mealIdeas.value = []
  } finally {
    mealIdeasLoading.value = false
  }
}

async function handleUndo(event: HistoryEvent) {
  if (undoingEventId.value !== null) return
  undoingEventId.value = event.id
  try {
    await undoEvent(event.id, crypto.randomUUID())
    await loadHistory()
    await inventoryStore.hydrateFromServer()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    undoingEventId.value = null
  }
}

function eventTypeLabel(type: HistoryEvent['eventType']): string {
  return t(`history.eventTypes.${type}`)
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  const diffHours = Math.floor(diffMs / 3_600_000)
  const diffDays = Math.floor(diffMs / 86_400_000)

  if (diffMins < 1) return locale.value === 'zh-CN' ? '刚刚' : 'just now'
  if (diffMins < 60) return locale.value === 'zh-CN' ? `${diffMins}分钟前` : `${diffMins}m ago`
  if (diffHours < 24) return locale.value === 'zh-CN' ? `${diffHours}小时前` : `${diffHours}h ago`
  if (diffDays < 7) return locale.value === 'zh-CN' ? `${diffDays}天前` : `${diffDays}d ago`
  return date.toLocaleDateString(locale.value === 'zh-CN' ? 'zh-CN' : 'en-US', { month: 'short', day: 'numeric' })
}

interface DisplaySnapshot {
  names?: { en?: string; 'zh-CN'?: string }
  quantity?: string
  unit?: string
  location?: string
  sessionName?: string
  originalEventType?: string
  items?: { foodKey?: string; quantity?: string; unit?: string; names?: { en?: string; 'zh-CN'?: string } }[]
}

function getFoodName(event: HistoryEvent): string {
  const snapshot = event.displaySnapshot as DisplaySnapshot
  const preferredLocale = locale.value === 'zh-CN' ? 'zh-CN' : 'en'
  if (snapshot.names?.[preferredLocale]) return snapshot.names[preferredLocale]
  if (snapshot.names?.en) return snapshot.names.en
  if (snapshot.names?.['zh-CN']) return snapshot.names['zh-CN']
  return event.foodKey
}

function formatQuantity(delta: string): string {
  const num = parseFloat(delta)
  if (isNaN(num)) return delta
  const sign = num > 0 ? '+' : ''
  return `${sign}${num}`
}

function locationLabel(location: string): string {
  const key = `storage.scopes.${location.toLowerCase()}`
  const translated = t(key)
  return translated === key ? location : translated
}

function buildDescription(event: HistoryEvent): string {
  const snapshot = event.displaySnapshot as DisplaySnapshot
  const foodName = getFoodName(event)
  const quantity = snapshot.quantity ?? event.quantityDelta
  const unit = snapshot.unit ?? ''
  const location = locationLabel(snapshot.location ?? '')
  const sessionName = snapshot.sessionName ?? ''
  const originalEventType = snapshot.originalEventType ?? ''

  switch (event.eventType) {
    case 'CHECK_IN':
      return t('history.descriptions.addedTo', { name: foodName, quantity, unit, location })
    case 'MANUAL_CONSUMPTION':
      return t('history.descriptions.usedFrom', { name: foodName, quantity, unit, location })
    case 'DISCARD':
      return t('history.descriptions.discardedFrom', { name: foodName, quantity, unit, location })
    case 'COOKING': {
      const itemCount = snapshot.items?.length ?? 0
      if (sessionName) return t('history.descriptions.cooked', { name: sessionName })
      if (itemCount > 0) return t('history.descriptions.cookedItems', { count: itemCount })
      return t('history.descriptions.cooked', { name: foodName })
    }
    case 'EDIT':
      return t('history.descriptions.edited')
    case 'MOVE':
      return t('history.descriptions.moved')
    case 'REVERSAL':
      return t('history.descriptions.reversed', { type: originalEventType || event.eventType })
    default:
      return foodName
  }
}

const showUndoButton = (event: HistoryEvent): boolean => {
  return event.reversible && event.eventType !== 'REVERSAL'
}

function getCookingItems(event: HistoryEvent): { foodKey?: string; name: string; quantity?: string; unit?: string }[] {
  const snapshot = event.displaySnapshot as DisplaySnapshot
  if (!snapshot.items) return []
  const preferredLocale = locale.value === 'zh-CN' ? 'zh-CN' : 'en'
  return snapshot.items.map((item) => ({
    foodKey: item.foodKey,
    name: item.names?.[preferredLocale] || item.names?.en || item.names?.['zh-CN'] || '',
    quantity: item.quantity,
    unit: item.unit,
  }))
}

function openMealIdea(session: RescueSession) {
  void clearNewMealIdea()
  void router.push(`/history/meal-idea/${session.sessionId}`)
}

watch(activeTab, (tab) => {
  if (tab === 'meal-ideas' && mealIdeas.value.length === 0) {
    void loadMealIdeas()
  }
})

onMounted(() => {
  const queryTab = route.query.tab
  if (queryTab === 'meal-ideas') {
    activeTab.value = 'meal-ideas'
    void loadMealIdeas()
  } else {
    void loadHistory()
  }
})
</script>

<template>
  <div class="history-view">
    <AppPageHeader :title="t('history.title')" />

    <div class="history-tabs">
      <button :class="{ active: activeTab === 'storage' }" @click="activeTab = 'storage'">
        {{ t('history.tabStorage') }}
        <span v-if="newMealIdea && activeTab === 'meal-ideas'" class="red-dot" />
      </button>
      <button :class="{ active: activeTab === 'meal-ideas' }" @click="activeTab = 'meal-ideas'">
        {{ t('mealIdeas.tabMealIdeas') }}
        <span v-if="newMealIdea" class="red-dot" />
      </button>
    </div>

    <!-- Storage tab content -->
    <template v-if="activeTab === 'storage'">
      <!-- Loading state -->
      <div v-if="loading" class="history-loading">
        <div class="history-loading__spinner" />
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="history-error">
        <p class="history-error__message">{{ t('history.loadError') }}</p>
        <AppButton variant="secondary" @click="loadHistory">
          {{ t('common.back') }}
        </AppButton>
      </div>

      <!-- Empty state -->
      <div v-else-if="events.length === 0" class="history-empty">
        <img class="history-empty__mark" src="/brand/fridge-pal-mark.svg" alt="" width="64" height="80">
        <p>{{ t('history.empty') }}</p>
      </div>

      <!-- Event list -->
      <ul v-else class="history-list" role="list">
        <li
          v-for="event in events"
          :key="event.id"
          class="history-event"
        >
          <div
            class="history-event__icon-wrap"
            :class="`history-event__icon-wrap--${event.eventType.toLowerCase().replace('_', '-')}`"
            :data-event-icon="eventIconMap[event.eventType]"
          >
            <AppIcon :name="eventIconMap[event.eventType]" :size="20" />
          </div>

          <div class="history-event__content">
            <div class="history-event__header">
              <span class="history-event__type">{{ eventTypeLabel(event.eventType) }}</span>
              <span class="history-event__time">{{ formatRelativeTime(event.createdAt) }}</span>
            </div>

            <p class="history-event__description">{{ buildDescription(event) }}</p>

            <div
              v-if="event.eventType !== 'COOKING' || getCookingItems(event).length"
              class="history-event__meta"
            >
              <template v-if="event.eventType === 'COOKING' && getCookingItems(event).length">
                <FoodToken
                  v-for="(item, i) in getCookingItems(event).slice(0, 5)"
                  :key="i"
                  :food-key="item.foodKey"
                  :name="item.name || item.foodKey || ''"
                  :size="24"
                />
                <span v-if="getCookingItems(event).length > 5" class="history-event__more">+{{ getCookingItems(event).length - 5 }}</span>
              </template>
              <template v-else>
                <FoodToken :food-key="event.foodKey" :name="getFoodName(event)" :size="28" />
                <span class="history-event__quantity">{{ formatQuantity(event.quantityDelta) }}</span>
              </template>
            </div>
          </div>

          <div class="history-event__actions">
            <AppButton
              v-if="showUndoButton(event)"
              variant="ghost"
              size="small"
              :disabled="undoingEventId === event.id"
              @click="handleUndo(event)"
            >
              <AppIcon v-if="undoingEventId === event.id" name="clock" :size="16" />
              <AppIcon v-else name="undo" :size="16" />
              {{ undoingEventId === event.id ? t('history.undoing') : t('history.undo') }}
            </AppButton>
          </div>
        </li>
      </ul>
    </template>

    <!-- Meal Ideas tab content -->
    <template v-else>
      <div v-if="mealIdeasLoading" class="history-loading">
        <div class="history-loading__spinner" />
      </div>

      <div v-else-if="mealIdeas.length === 0" class="history-empty">
        <img class="history-empty__mark" src="/brand/fridge-pal-mark.svg" alt="" width="64" height="80">
        <p>{{ t('mealIdeas.empty') }}</p>
      </div>

      <ul v-else class="meal-ideas-list" role="list">
        <li
          v-for="(session, index) in mealIdeas"
          :key="session.sessionId"
          class="meal-idea-card"
          role="button"
          tabindex="0"
          @click="openMealIdea(session)"
          @keydown.enter="openMealIdea(session)"
        >
          <div class="meal-idea-card__header">
            <span v-if="newMealIdea && index === 0" class="meal-idea-card__new">{{ t('mealIdeas.new') }}</span>
            <span class="meal-idea-card__time">{{ formatRelativeTime(session.searchedAt || session.createdAt) }}</span>
          </div>

          <div class="meal-idea-card__foods">
            <FoodToken
              v-for="food in session.selectedFoods.slice(0, 5)"
              :key="food.foodKey"
              :food-key="food.foodKey"
              :name="food.names?.en || food.names?.['zh-CN'] || food.foodKey"
              :size="32"
            />
          </div>

          <div class="meal-idea-card__footer">
            <span v-if="session.recipes?.[0]?.title" class="meal-idea-card__title">{{ session.recipes[0].title }}</span>
            <span v-if="session.cuisine" class="meal-idea-card__cuisine">{{ t(`rescue.cuisine.${session.cuisine}`) }}</span>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.history-view {
  width: min(100%, 940px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
}

.history-tabs {
  display: flex;
  gap: var(--space-1);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border);
}

.history-tabs button {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-muted);
  background: transparent;
  transition: color var(--duration-base) var(--ease-standard);
}

.history-tabs button:hover {
  color: var(--color-ink);
}

.history-tabs button.active {
  color: var(--color-primary);
  background: var(--color-primary-softer);
}

.red-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.history-loading {
  display: grid;
  min-height: calc(100vh - 72px);
  place-items: center;
}

.history-loading__spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.history-error {
  display: grid;
  min-height: calc(100vh - 72px);
  place-items: center;
  gap: var(--space-4);
  text-align: center;
  padding: var(--space-6);
}

.history-error__message {
  color: var(--color-muted);
}

.history-empty {
  display: grid;
  min-height: calc(100vh - 72px);
  place-items: center;
  align-content: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-5);
  border-radius: var(--radius-card);
  text-align: center;
  color: var(--color-muted);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.history-empty__mark {
  width: 64px;
  height: 80px;
}

.history-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) 0;
}

.history-event {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-sm);
}

.history-event__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: none;
  background: var(--color-primary-soft);
  border-radius: var(--radius-md);
  color: var(--color-primary);
}

.history-event__icon-wrap--discard,
.history-event__icon-wrap--manual-consumption {
  color: var(--color-muted);
  background: var(--color-surface-muted, var(--color-primary-softer));
}

.history-event__icon-wrap--reversal {
  color: var(--color-ink);
  background: var(--color-primary-softer);
}

.history-event__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.history-event__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.history-event__type {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.history-event__time {
  font-size: var(--font-size-xs);
  color: var(--color-muted);
  flex-shrink: 0;
}

.history-event__description {
  font-size: var(--font-size-base);
  color: var(--color-ink);
  margin: 0;
}

.history-event__meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.history-event__quantity {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-muted);
}

.history-event__more {
  font-size: var(--font-size-xs);
  color: var(--color-muted);
  font-weight: var(--font-weight-semibold);
}

.history-event__actions {
  flex: none;
  display: flex;
  align-items: center;
}

.meal-ideas-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) 0;
}

.meal-idea-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: box-shadow var(--duration-base) var(--ease-standard), transform var(--duration-base) var(--ease-standard);
}

.meal-idea-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.meal-idea-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meal-idea-card__new {
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-danger);
  color: white;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.meal-idea-card__time {
  font-size: var(--font-size-xs);
  color: var(--color-muted);
}

.meal-idea-card__foods {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.meal-idea-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.meal-idea-card__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meal-idea-card__cuisine {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
  flex-shrink: 0;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-primary-softer);
}

@media (min-width: 880px) {
  .history-event {
    padding: var(--space-4) var(--space-5);
  }

  .history-event__description {
    font-size: var(--font-size-lg);
  }

  .history-list {
    gap: var(--space-3);
  }
}
</style>
