<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppPageHeader from '../components/AppPageHeader.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import { useRescueStore } from '../features/rescue/rescueStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t } = useI18n()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedFoods, selectedIds, removeFood, replaceSelection } = useRescueStore(inventory)
const recentSection = ref<HTMLElement | null>(null)

const recentFixtures = [
  {
    titleKey: 'rescue.recentHighProtein',
    foodKeys: ['chicken-breast', 'tofu', 'eggs', 'broccoli', 'spinach'],
  },
  {
    titleKey: 'rescue.recentFresh',
    foodKeys: ['spinach', 'broccoli', 'mushrooms', 'lemon', 'tomatoes', 'carrots', 'tofu'],
  },
]

const recentSearches = computed(() =>
  recentFixtures.map((item) => ({
    ...item,
    foods: item.foodKeys
      .map((foodKey) => inventory.value.find((food) => food.foodKey === foodKey))
      .filter((food) => food !== undefined),
  })),
)

onMounted(() => {
  void hydrateFromServer()
})

function openRecent(foodIds: string[]) {
  replaceSelection(foodIds)
  void router.push('/rescue/results')
}
</script>

<template>
  <div class="rescue-view">
    <AppPageHeader :title="t('rescue.title')">
      <template #actions>
        <button class="recent-action" type="button" @click="recentSection?.scrollIntoView({ block: 'start' })">
          {{ t('rescue.recent') }}
        </button>
      </template>
    </AppPageHeader>

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

      <section ref="recentSection" class="recent-searches">
        <h2>{{ t('rescue.continueTitle') }}</h2>
        <div class="recent-card-row">
          <button
            v-for="item in recentSearches"
            :key="item.titleKey"
            type="button"
            :aria-label="t('rescue.continueSearch', { name: t(item.titleKey) })"
            @click="openRecent(item.foods.map((food) => food.id))"
          >
            <span class="recent-card__tokens" aria-hidden="true">
              <FoodToken
                v-for="food in item.foods.slice(0, 4)"
                :key="food.id"
                :food-key="food.foodKey"
                :name="t(food.nameKey)"
                :size="30"
              />
            </span>
            <span class="recent-card__copy">
              <strong>{{ t(item.titleKey) }}</strong>
              <span>{{ t('rescue.foodCount', { count: item.foods.length }) }}</span>
            </span>
            <span class="recent-card__arrow" aria-hidden="true">›</span>
          </button>
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

.recent-action {
  min-height: var(--tap-target-min);
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

.recent-card-row > button {
  display: grid;
  min-width: 0;
  min-height: 126px;
  grid-template-columns: 1fr auto;
  align-content: space-between;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  text-align: left;
  transition: box-shadow var(--duration-base) var(--ease-standard), transform var(--duration-base) var(--ease-standard);
}

.recent-card-row > button:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.recent-card__tokens {
  display: flex;
  grid-column: 1 / -1;
  gap: 3px;
}

.recent-card__copy {
  display: grid;
  min-width: 0;
}

.recent-card__copy strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-card__copy > span {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.recent-card__arrow {
  align-self: end;
  color: var(--color-primary);
  font-size: var(--font-size-xl);
  line-height: 1;
}

@media (min-width: 880px) {
  .recent-card-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
