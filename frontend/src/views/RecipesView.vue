<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import { useRecipeStore, type SavedRecipe } from '../features/recipes/recipeStore'

type SortMode = 'recent' | 'name'

const { t, locale } = useI18n()
const router = useRouter()
const { savedRecipes } = useRecipeStore()
const query = ref('')
const sortMode = ref<SortMode>('recent')

const visibleRecipes = computed(() => {
  const normalized = query.value.trim().toLocaleLowerCase(locale.value)
  const matching = savedRecipes.value.filter((recipe) => {
    const haystack = `${recipe.name} ${recipe.description}`.toLocaleLowerCase(locale.value)
    return !normalized || haystack.includes(normalized)
  })
  return [...matching].sort((left, right) =>
    sortMode.value === 'name'
      ? left.name.localeCompare(right.name, locale.value)
      : right.savedAt.localeCompare(left.savedAt),
  )
})

function openRecipe(recipe: SavedRecipe) {
  void router.push({ path: '/recipes/editor', query: { origin: recipe.originId, savedId: recipe.id } })
}
</script>

<template>
  <div class="recipes-view">
    <header class="recipes-header">
      <div>
        <span>{{ t('app.title') }}</span>
        <h1>{{ t('recipes.title') }}</h1>
      </div>
      <span>{{ t('recipes.savedCount', { count: savedRecipes.length }) }}</span>
    </header>

    <main class="recipes-content">
      <section class="recipes-intro">
        <h2>{{ t('recipes.framing') }}</h2>
        <p>{{ t('recipes.subtitle') }}</p>
      </section>

      <div class="recipes-toolbar">
        <label>
          <span class="sr-only">{{ t('recipes.search') }}</span>
          <input v-model="query" type="search" :placeholder="t('recipes.searchPlaceholder')">
        </label>
        <label>
          <span class="sr-only">{{ t('recipes.sort') }}</span>
          <select v-model="sortMode">
            <option value="recent">{{ t('recipes.sortRecent') }}</option>
            <option value="name">{{ t('recipes.sortName') }}</option>
          </select>
        </label>
      </div>

      <div v-if="visibleRecipes.length" class="recipe-list stagger-in">
        <article v-for="recipe in visibleRecipes" :key="recipe.id" class="saved-recipe-card">
          <button class="saved-recipe-card__open" type="button" @click="openRecipe(recipe)">
            <span class="saved-recipe-card__tokens" :aria-label="t('recipes.ingredientPreview')">
              <FoodToken
                v-for="ingredient in recipe.ingredients.slice(0, 6)"
                :key="ingredient.id"
                :food-key="ingredient.foodKey"
                :name="t(ingredient.nameKey)"
                :size="40"
              />
            </span>
            <span class="saved-recipe-card__copy">
              <span>{{ t(`recipes.origins.${recipe.originType}`) }}</span>
              <strong>{{ recipe.name }}</strong>
              <span class="saved-recipe-card__description">{{ recipe.description }}</span>
              <small v-if="recipe.lastCookedPortion">{{ t('recipes.lastCooked', { count: recipe.lastCookedPortion }) }}</small>
            </span>
          </button>
          <AppButton size="small" @click.stop="openRecipe(recipe)">{{ t('recipes.cookAgain') }}</AppButton>
        </article>
      </div>

      <section v-else class="recipes-empty">
        <h2>{{ t('recipes.emptyTitle') }}</h2>
        <p>{{ t('recipes.emptyDescription') }}</p>
        <AppButton @click="router.push('/rescue')">{{ t('recipes.findIdeas') }}</AppButton>
      </section>
    </main>
  </div>
</template>

<style scoped>
.recipes-view {
  width: min(100%, 940px);
  min-height: 100vh;
  padding: 0 var(--space-3) 96px;
  margin: 0 auto;
}

.recipes-header {
  display: flex;
  min-height: 82px;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-top: var(--safe-area-top);
  border-bottom: 1px solid var(--color-border);
}

.recipes-header > div > span,
.recipes-header > span {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.recipes-header h1 {
  font-size: var(--font-size-2xl);
}

.recipes-content {
  display: grid;
  gap: var(--space-5);
  padding-top: var(--space-5);
}

.recipes-intro p {
  margin-top: var(--space-1);
  color: var(--color-muted);
}

.recipes-toolbar {
  display: grid;
  grid-template-columns: 1fr 148px;
  gap: var(--space-2);
}

.recipes-toolbar input,
.recipes-toolbar select {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.recipe-list {
  display: grid;
  gap: var(--space-3);
}

.saved-recipe-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.saved-recipe-card__open {
  display: grid;
  min-width: 0;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: var(--space-4);
  text-align: left;
  cursor: pointer;
}

.saved-recipe-card__tokens {
  display: grid;
  width: 88px;
  grid-template-columns: repeat(2, 40px);
  gap: 4px;
}

.saved-recipe-card__copy {
  display: block;
  min-width: 0;
}

.saved-recipe-card__copy > span,
.saved-recipe-card__copy small {
  color: var(--color-muted);
  font-size: var(--font-size-xs);
}

.saved-recipe-card__copy > strong {
  display: block;
  margin-top: 2px;
  font-size: var(--font-size-xl);
  line-height: var(--line-height-tight);
}

.saved-recipe-card__description {
  display: -webkit-box;
  margin: var(--space-1) 0;
  overflow: hidden;
  color: var(--color-ink-soft);
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recipes-empty {
  display: grid;
  max-width: 440px;
  justify-items: start;
  gap: var(--space-3);
  padding: var(--space-10) var(--space-5);
  margin: var(--space-8) auto 0;
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.recipes-empty p {
  color: var(--color-muted);
}

@media (max-width: 620px) {
  .saved-recipe-card {
    grid-template-columns: 1fr;
    align-items: start;
    gap: var(--space-3);
  }

  .saved-recipe-card__open {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .saved-recipe-card__tokens {
    width: 64px;
    grid-template-columns: repeat(2, 30px);
  }

  .saved-recipe-card__tokens :deep(.food-token) {
    width: 30px !important;
    height: 30px !important;
  }
}
</style>
