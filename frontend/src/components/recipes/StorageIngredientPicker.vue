<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { InventoryFood, StorageLocation } from '../../features/storage/inventory'
import AppChip from '../AppChip.vue'
import FoodToken from '../food-token/FoodToken.vue'

type Scope = 'all' | StorageLocation

const props = defineProps<{
  open: boolean
  foods: InventoryFood[]
  ingredientIds: Set<string>
}>()

const emit = defineEmits<{
  close: []
  confirm: [foodIds: string[]]
}>()

const { t, locale } = useI18n()
const scopes: Scope[] = ['all', 'fridge', 'freezer', 'pantry']
const scope = ref<Scope>('all')
const query = ref('')
const pendingIds = ref<string[]>([])
const searchInput = ref<HTMLInputElement | null>(null)
let previousBodyOverflow = ''

const visibleFoods = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  return props.foods.filter((food) => {
    const inScope = scope.value === 'all' || food.location === scope.value
    const matchesQuery = !normalized || t(food.nameKey).toLocaleLowerCase(locale.value).includes(normalized)
    return inScope && matchesQuery
  })
})

watch(
  () => props.open,
  async (open) => {
    if (open) {
      pendingIds.value = []
      scope.value = 'all'
      query.value = ''
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      await nextTick()
      searchInput.value?.focus()
    } else {
      document.body.style.overflow = previousBodyOverflow
    }
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow
})

function isPending(foodId: string) {
  return pendingIds.value.includes(foodId)
}

function toggle(foodId: string) {
  if (props.ingredientIds.has(foodId)) return
  const index = pendingIds.value.indexOf(foodId)
  if (index >= 0) pendingIds.value.splice(index, 1)
  else pendingIds.value.push(foodId)
}

function close() {
  emit('close')
}

function confirm() {
  if (pendingIds.value.length === 0) return
  emit('confirm', [...pendingIds.value])
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="ingredient-picker-overlay" @click.self="close" @keydown="onKeydown">
      <section class="ingredient-picker sheet-up" role="dialog" aria-modal="true" :aria-labelledby="'ingredient-picker-title'">
        <header class="ingredient-picker__header">
          <button type="button" :aria-label="t('common.back')" @click="close">×</button>
          <div>
            <h2 id="ingredient-picker-title">{{ t('recipeEditor.chooseStorageFoods') }}</h2>
            <span>{{ t('recipeEditor.selectedToAdd', { count: pendingIds.length }) }}</span>
          </div>
          <span aria-hidden="true" />
        </header>

        <div class="ingredient-picker__toolbar">
          <div class="ingredient-picker__scopes">
            <AppChip v-for="item in scopes" :key="item" :selected="scope === item" @toggle="scope = item">
              {{ t(`storage.scopes.${item}`) }}
            </AppChip>
          </div>
          <label>
            <span class="sr-only">{{ t('storage.search') }}</span>
            <input ref="searchInput" v-model="query" type="search" :placeholder="t('storage.searchPlaceholder')">
          </label>
        </div>

        <div class="ingredient-picker__body">
          <div v-if="visibleFoods.length" class="ingredient-picker__grid stagger-in">
            <button
              v-for="food in visibleFoods"
              :key="food.id"
              type="button"
              class="ingredient-picker__food"
              :class="{ 'ingredient-picker__food--selected': isPending(food.id) }"
              :disabled="ingredientIds.has(food.id)"
              :aria-pressed="isPending(food.id)"
              :aria-label="ingredientIds.has(food.id) ? `${t(food.nameKey)}, ${t('recipeEditor.inRecipe')}` : t(food.nameKey)"
              @click="toggle(food.id)"
            >
              <span v-if="isPending(food.id)" class="ingredient-picker__check" aria-hidden="true">✓</span>
              <FoodToken :food-key="food.foodKey" :name="t(food.nameKey)" :size="52" />
              <span>{{ t(food.nameKey) }}</span>
              <small v-if="ingredientIds.has(food.id)">{{ t('recipeEditor.inRecipe') }}</small>
            </button>
          </div>
          <p v-else class="ingredient-picker__empty">{{ t('recipeEditor.noStorageMatches') }}</p>
        </div>

        <footer class="ingredient-picker__footer">
          <p>{{ t('recipeEditor.newIngredientsHint') }}</p>
          <button type="button" :disabled="pendingIds.length === 0" @click="confirm">
            {{ t('recipeEditor.addIngredients', { count: pendingIds.length }) }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.ingredient-picker-overlay {
  position: fixed;
  z-index: var(--z-dialog);
  inset: 0;
  background: rgb(8 18 38 / 0.42);
}

.ingredient-picker {
  display: grid;
  width: 100%;
  height: 100dvh;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  background: var(--color-canvas);
}

.ingredient-picker__header {
  display: grid;
  min-height: 68px;
  grid-template-columns: 64px 1fr 64px;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  text-align: center;
}

.ingredient-picker__header button {
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.ingredient-picker__header button:first-child {
  font-size: 1.8rem;
}

.ingredient-picker__header h2 {
  font-size: var(--font-size-lg);
}

.ingredient-picker__header span {
  display: block;
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.ingredient-picker__toolbar {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.ingredient-picker__scopes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-1);
}

.ingredient-picker__toolbar input {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.ingredient-picker__body {
  padding: var(--space-3);
  overflow-y: auto;
}

.ingredient-picker__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-2);
}

.ingredient-picker__food {
  position: relative;
  display: flex;
  min-width: 0;
  min-height: 120px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.ingredient-picker__food--selected {
  background: var(--color-primary-softer);
  box-shadow: inset 0 0 0 2px var(--color-primary), var(--shadow-sm);
}

.ingredient-picker__food:disabled {
  opacity: 0.42;
}

.ingredient-picker__food > span:not(.ingredient-picker__check) {
  width: 100%;
  overflow: hidden;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ingredient-picker__food small {
  color: var(--color-muted);
  font-size: 0.625rem;
}

.ingredient-picker__check {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: var(--radius-full);
  color: var(--color-on-primary);
  background: var(--color-primary);
}

.ingredient-picker__empty {
  padding: var(--space-10) var(--space-4);
  color: var(--color-muted);
  text-align: center;
}

.ingredient-picker__footer {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3) max(var(--space-3), var(--safe-area-right)) calc(var(--space-3) + var(--safe-area-bottom)) max(var(--space-3), var(--safe-area-left));
  background: var(--color-nav-bg);
  border-top: 1px solid var(--color-border);
}

.ingredient-picker__footer p {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  text-align: center;
}

.ingredient-picker__footer button {
  min-height: 52px;
  border-radius: var(--radius-lg);
  color: var(--color-on-primary);
  background: var(--color-primary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
}

.ingredient-picker__footer button:disabled {
  opacity: 0.45;
}

@media (min-width: 720px) {
  .ingredient-picker-overlay {
    display: grid;
    place-items: center;
    padding: var(--space-8);
  }

  .ingredient-picker {
    width: min(920px, 100%);
    height: min(760px, calc(100dvh - 64px));
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-overlay);
    overflow: hidden;
  }

  .ingredient-picker__toolbar {
    grid-template-columns: 1fr 280px;
  }

  .ingredient-picker__grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .ingredient-picker__footer {
    grid-template-columns: 1fr auto;
    align-items: center;
  }

  .ingredient-picker__footer p {
    text-align: left;
  }

  .ingredient-picker__footer button {
    min-width: 220px;
    padding: 0 var(--space-5);
  }
}
</style>
