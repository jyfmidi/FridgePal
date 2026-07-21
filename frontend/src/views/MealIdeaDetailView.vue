<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppIcon from '../components/AppIcon.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import type { Recipe, RescueSession } from '../api/rescue'
import { fetchRescueSession } from '../api/rescue'
import { useInventoryStore } from '../features/storage/inventoryStore'
import { useRescueStore } from '../features/rescue/rescueStore'
import { formatRecipeAmount, isSeasoning, formatSeasoningAmount } from '../features/recipes/unitConversion'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const inventoryStore = useInventoryStore()
const { clearNewMealIdea } = useRescueStore(inventoryStore.inventory)

const session = ref<RescueSession | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const recipes = computed<Recipe[]>(() => session.value?.recipes ?? [])
const searchSessionId = computed(() => session.value?.sessionId ?? '')

const selectedFoods = computed(() => {
  if (!session.value) return []
  return session.value.selectedFoods.map((f) => ({
    id: `${f.foodKey}-${f.location}`,
    foodKey: f.foodKey,
    nameKey: `foods.${f.foodKey.replace(/-/g, '')}`,
    names: { en: f.names.en ?? f.foodKey, 'zh-CN': f.names['zh-CN'] ?? '' },
    quantity: parseFloat(f.quantity),
    unit: f.unit,
    location: f.location.toLowerCase() as 'fridge' | 'freezer' | 'pantry',
    urgency: 'neutral' as const,
  }))
})

async function loadSession() {
  loading.value = true
  error.value = null
  try {
    const sessionId = route.params.sessionId as string
    session.value = await fetchRescueSession(sessionId)
  } catch {
    error.value = 'Could not load meal idea.'
  } finally {
    loading.value = false
  }
}

function editRecipe(recipeIndex: number) {
  void router.push({
    path: '/recipes/editor',
    query: { origin: `recipe-${recipeIndex}`, sessionId: searchSessionId.value },
  })
}

function mainIngredients(recipe: Recipe) {
  return recipe.ingredients.filter((ing) => !isSeasoning(ing))
}

function seasoningIngredients(recipe: Recipe) {
  return recipe.ingredients.filter((ing) => isSeasoning(ing))
}

onMounted(() => {
  void loadSession()
  clearNewMealIdea()
})
</script>

<template>
  <div class="detail-view">
    <AppTaskHeader :title="t('recipeResults.title')" :back-label="t('common.back')" @back="router.push('/history')">
      <template #action>
        <button class="header-action" type="button" @click="router.push('/rescue/choose')">
          <AppIcon name="swap" :size="17" />
          {{ t('recipeResults.changeFoods') }}
        </button>
      </template>
    </AppTaskHeader>

    <main class="detail-content">
      <div v-if="loading" class="detail-loading">
        <p>{{ t('recipeResults.loading') }}</p>
      </div>

      <div v-else-if="error" class="detail-error">
        <p>{{ error }}</p>
      </div>

      <template v-else>
        <section class="using-strip" aria-labelledby="using-title">
          <div class="section-heading">
            <h1 id="using-title">{{ t('recipeResults.using') }}</h1>
            <span>{{ selectedFoods.length }}/7</span>
          </div>
          <SelectionRail :foods="selectedFoods" />
        </section>

        <section class="recipe-section" aria-labelledby="recipes-title">
          <div class="recipe-section__heading">
            <h2 id="recipes-title">{{ t('recipeResults.title') }}</h2>
            <span v-if="session?.cuisine" class="recipe-section__cuisine">{{ t(`rescue.cuisine.${session.cuisine}`) }}</span>
          </div>

          <article v-for="(recipe, idx) in recipes" :key="idx" class="recipe-card">
            <h3>{{ recipe.title }}</h3>
            <span class="recipe-card__ai-badge">{{ t('recipeResults.aiGenerated') }}</span>
            <p v-if="recipe.description" class="recipe-card__desc">{{ recipe.description }}</p>

            <div class="recipe-card__yield">
              <span>{{ t('recipeResults.baseYield') }}</span>
              <strong>{{ recipe.baseYield }}</strong>
            </div>

            <h4>{{ t('recipeResults.ingredients') }}</h4>
            <div class="ingredient-grid">
              <div v-for="(ing, i) in mainIngredients(recipe)" :key="i">
                <span>{{ ing.originalText }}</span>
                <strong>{{ formatRecipeAmount(ing.amount, ing.unit) }}</strong>
              </div>
            </div>

            <div v-if="seasoningIngredients(recipe).length" class="seasoning-section">
              <h4 class="seasoning-section__title">{{ t('recipeResults.seasonings') }}</h4>
              <div class="seasoning-grid">
                <div v-for="(ing, i) in seasoningIngredients(recipe)" :key="i" class="seasoning-item">
                  <span>{{ ing.originalText }}</span>
                  <strong v-if="formatSeasoningAmount(ing.amount, ing.unit)">{{ formatSeasoningAmount(ing.amount, ing.unit) }}</strong>
                </div>
              </div>
            </div>

            <h4>{{ t('recipeResults.steps') }}</h4>
            <ol class="step-list">
              <li v-for="(step, i) in recipe.steps" :key="i">{{ step }}</li>
            </ol>

            <div class="recipe-card__actions">
              <AppButton size="small" @click="editRecipe(idx)">
                <AppIcon name="edit" :size="17" />
                {{ t('recipeResults.editRecipe') }}
              </AppButton>
            </div>
          </article>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.detail-view {
  width: min(100%, 880px);
  min-height: 100vh;
  padding: 0 var(--space-3) 100px;
  margin: 0 auto;
}

.detail-content {
  display: grid;
  gap: var(--space-8);
  padding-top: var(--space-5);
}

.detail-loading,
.detail-error {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  text-align: center;
  place-items: center;
}

.header-action {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.using-strip {
  position: sticky;
  z-index: calc(var(--z-sticky) - 1);
  top: calc(64px + var(--safe-area-top));
  padding: var(--space-2) 0 var(--space-3);
  color: var(--color-ink);
  background: var(--color-header-bg);
  backdrop-filter: blur(14px);
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.section-heading h1 {
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.section-heading span {
  color: var(--color-selection-muted);
  font-size: var(--font-size-xs);
}

.using-strip :deep(.selection-rail) {
  margin-top: var(--space-2);
}

.recipe-section {
  display: grid;
  gap: var(--space-4);
}

.recipe-section__heading {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.recipe-section__cuisine {
  padding: 2px var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-primary-softer);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.recipe-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-5);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.recipe-card h3 {
  font-size: var(--font-size-2xl);
}

.recipe-card__ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-primary-softer);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  width: fit-content;
}

.recipe-card__desc {
  color: var(--color-muted);
}

.recipe-card__yield {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-primary-softer);
}

.recipe-card__yield span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.recipe-card h4 {
  padding-top: var(--space-2);
  font-size: var(--font-size-lg);
}

.ingredient-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.ingredient-grid > div {
  display: flex;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-canvas);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.ingredient-grid span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.seasoning-section {
  display: grid;
  gap: var(--space-2);
}

.seasoning-section__title {
  padding-top: var(--space-2);
  font-size: var(--font-size-base);
  color: var(--color-muted);
}

.seasoning-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seasoning-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-canvas);
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-size: var(--font-size-sm);
}

.seasoning-item span {
  color: var(--color-ink-soft);
}

.seasoning-item strong {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.step-list {
  display: grid;
  gap: var(--space-3);
  padding-left: var(--space-6);
  list-style: decimal;
}

.step-list li {
  padding-left: var(--space-1);
}

.recipe-card__actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}

@media (min-width: 700px) {
  .ingredient-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 420px) {
  .recipe-card {
    padding: var(--space-4);
  }

  .recipe-card__actions {
    flex-direction: column;
  }
}
</style>
