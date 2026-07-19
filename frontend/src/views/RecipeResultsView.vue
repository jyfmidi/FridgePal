<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppIcon from '../components/AppIcon.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import RecipeMatchBelt from '../components/recipes/RecipeMatchBelt.vue'
import SelectionRail from '../components/rescue/SelectionRail.vue'
import { buildPlanIngredients, recipeSources } from '../features/recipes/fixtures'
import { useRescueStore } from '../features/rescue/rescueStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t } = useI18n()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedFoods } = useRescueStore(inventory)
const ingredients = computed(() => buildPlanIngredients(selectedFoods.value))

onMounted(() => {
  void hydrateFromServer()
})

function editRecipe(origin: string) {
  void router.push({ path: '/recipes/editor', query: { origin } })
}
</script>

<template>
  <div class="results-view">
    <AppTaskHeader :title="t('recipeResults.title')" :back-label="t('common.back')" @back="router.push('/rescue')">
      <template #action>
        <button class="header-action" type="button" @click="router.push('/rescue/choose')">
          <AppIcon name="swap" :size="17" />
          {{ t('recipeResults.changeFoods') }}
        </button>
      </template>
    </AppTaskHeader>

    <main class="results-content">
      <section class="using-strip" aria-labelledby="using-title">
        <div class="section-heading">
          <h1 id="using-title">{{ t('recipeResults.using') }}</h1>
          <span>{{ selectedFoods.length }}/7</span>
        </div>
        <SelectionRail :foods="selectedFoods" />
      </section>

      <section class="source-section stagger-in" aria-labelledby="sources-title">
        <div class="section-copy">
          <h2 id="sources-title">{{ t('recipeResults.sources') }}</h2>
          <p>{{ t('recipeResults.sourcesHint') }}</p>
        </div>

        <article v-for="source in recipeSources" :key="source.id" class="source-card">
          <div class="source-card__topline">
            <span>{{ source.publisher }}</span>
            <span>{{ source.domain }}</span>
          </div>
          <h3>{{ source.title }}</h3>
          <RecipeMatchBelt :foods="selectedFoods" :used-food-keys="source.usedFoodKeys" />
          <div class="source-card__actions">
            <a :href="source.url" target="_blank" rel="noopener noreferrer">
              <AppIcon name="globe" :size="18" />
              {{ t('recipeResults.website') }}
            </a>
            <AppButton size="small" @click="editRecipe(source.id)">
              <AppIcon name="edit" :size="17" />
              {{ t('recipeResults.editRecipe') }}
            </AppButton>
          </div>
        </article>
      </section>

      <section class="ai-plan" aria-labelledby="ai-plan-title">
        <div class="ai-plan__eyebrow">
          <span aria-hidden="true">✦</span>
          <strong>{{ t('recipeResults.aiLabel') }}</strong>
        </div>
        <h2 id="ai-plan-title">{{ t('recipeResults.aiTitle') }}</h2>
        <p class="ai-plan__description">{{ t('recipeResults.aiDescription') }}</p>

        <div class="ai-plan__yield">
          <span>{{ t('recipeResults.baseYield') }}</span>
          <strong>{{ t('recipeResults.servings', { count: 2 }) }}</strong>
        </div>

        <h3>{{ t('recipeResults.ingredients') }}</h3>
        <div class="ingredient-grid">
          <div v-for="ingredient in ingredients" :key="ingredient.id">
            <span>{{ t(ingredient.nameKey) }}</span>
            <strong>{{ ingredient.amount }}</strong>
          </div>
          <div class="ingredient-grid__pantry">
            <span>{{ t('recipeResults.pantryStaples') }}</span>
            <strong>Oil, salt, pepper</strong>
          </div>
        </div>

        <h3>{{ t('recipeResults.steps') }}</h3>
        <ol class="step-list">
          <li>{{ t('recipeResults.stepOne') }}</li>
          <li>{{ t('recipeResults.stepTwo') }}</li>
          <li>{{ t('recipeResults.stepThree') }}</li>
        </ol>

        <div class="ai-plan__footer">
          <span>{{ t('recipeResults.sourceCount', { count: recipeSources.length }) }}</span>
          <AppButton @click="editRecipe('ai-plan')">
            <AppIcon name="edit" :size="18" />
            {{ t('recipeResults.editRecipe') }}
          </AppButton>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.results-view {
  width: min(100%, 880px);
  min-height: 100vh;
  padding: 0 var(--space-3) 100px;
  margin: 0 auto;
}

.results-content {
  display: grid;
  gap: var(--space-8);
  padding-top: var(--space-5);
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

.section-heading,
.source-card__topline,
.source-card__actions,
.ai-plan__yield,
.ai-plan__footer {
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

.source-section {
  display: grid;
  gap: var(--space-3);
}

.section-copy p,
.ai-plan__description {
  margin-top: var(--space-1);
  color: var(--color-muted);
}

.source-card {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.source-card__topline {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.source-card h3 {
  font-size: var(--font-size-xl);
}

.source-card__actions {
  padding-top: var(--space-1);
}

.source-card__actions a {
  min-height: var(--tap-target-min);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: var(--font-weight-semibold);
}

.ai-plan {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border: 1px solid var(--color-primary-soft);
  border-radius: var(--radius-xl);
  background: var(--color-primary-softer);
  box-shadow: var(--shadow-md);
}

.ai-plan__eyebrow {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.ai-plan h2 {
  font-size: var(--font-size-2xl);
}

.ai-plan h3 {
  padding-top: var(--space-2);
  font-size: var(--font-size-lg);
}

.ai-plan__yield {
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: rgb(255 255 255 / 0.72);
}

.ai-plan__yield span,
.ai-plan__footer > span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.ingredient-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.ingredient-grid > div {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.ingredient-grid span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.ingredient-grid__pantry {
  grid-column: 1 / -1;
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

.ai-plan__footer {
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-primary-soft);
}

@media (min-width: 700px) {
  .source-section {
    grid-template-columns: 1fr 1fr;
  }

  .source-section .section-copy,
  .source-section .source-card:first-of-type {
    grid-column: 1 / -1;
  }

  .ingredient-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .ingredient-grid__pantry {
    grid-column: auto;
  }
}

@media (max-width: 420px) {
  .source-card,
  .ai-plan {
    padding: var(--space-4);
  }

  .ai-plan__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .source-card__actions {
    align-items: stretch;
    flex-direction: column;
  }

  .source-card__actions a {
    justify-content: center;
  }
}
</style>
