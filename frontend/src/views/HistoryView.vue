<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppPageHeader from '../components/AppPageHeader.vue'
import AppButton from '../components/AppButton.vue'
import AppIcon, { type AppIconName } from '../components/AppIcon.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { fetchHistory, undoEvent, type HistoryEvent } from '../api/history'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t, locale } = useI18n()
const inventoryStore = useInventoryStore()

const events = ref<HistoryEvent[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const undoingEventId = ref<string | null>(null)

const eventIconMap: Record<HistoryEvent['eventType'], AppIconName> = {
  CHECK_IN: 'add',
  EDIT: 'edit',
  MOVE: 'swap',
  MANUAL_CONSUMPTION: 'remove',
  COOKING: 'chef',
  DISCARD: 'trash',
  REVERSAL: 'undo',
}

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
  items?: unknown[]
}

function getFoodName(event: HistoryEvent): string {
  const snapshot = event.displaySnapshot as DisplaySnapshot
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

function buildDescription(event: HistoryEvent): string {
  const snapshot = event.displaySnapshot as DisplaySnapshot
  const foodName = getFoodName(event)
  const quantity = snapshot.quantity ?? event.quantityDelta
  const unit = snapshot.unit ?? ''
  const location = snapshot.location ?? ''
  const sessionName = snapshot.sessionName ?? ''
  const originalEventType = snapshot.originalEventType ?? ''

  switch (event.eventType) {
    case 'CHECK_IN':
      return t('history.descriptions.addedTo', { quantity, unit, location })
    case 'MANUAL_CONSUMPTION':
      return t('history.descriptions.usedFrom', { quantity, unit, location })
    case 'DISCARD':
      return t('history.descriptions.discardedFrom', { quantity, unit, location })
    case 'COOKING':
      return t('history.descriptions.cooked', { name: sessionName || foodName })
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

onMounted(loadHistory)
</script>

<template>
  <div class="history-view">
    <AppPageHeader :title="t('history.title')" />

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
      <p>{{ t('history.empty') }}</p>
    </div>

    <!-- Event list -->
    <ul v-else class="history-list" role="list">
      <li
        v-for="event in events"
        :key="event.id"
        class="history-event"
      >
        <div class="history-event__icon-wrap">
          <AppIcon :name="eventIconMap[event.eventType]" :size="20" />
        </div>

        <div class="history-event__content">
          <div class="history-event__header">
            <span class="history-event__type">{{ eventTypeLabel(event.eventType) }}</span>
            <span class="history-event__time">{{ formatRelativeTime(event.createdAt) }}</span>
          </div>

          <p class="history-event__description">{{ buildDescription(event) }}</p>

          <div class="history-event__meta">
            <FoodToken :name="getFoodName(event)" :size="24" />
            <span class="history-event__quantity">{{ formatQuantity(event.quantityDelta) }}</span>
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
  </div>
</template>

<style scoped>
.history-view {
  width: min(100%, 940px);
  min-height: 100vh;
  padding: 0 var(--space-3) 88px;
  margin: 0 auto;
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
  text-align: center;
  color: var(--color-muted);
  padding: var(--space-6);
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
  color: var(--color-text);
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

.history-event__actions {
  flex: none;
  display: flex;
  align-items: center;
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
