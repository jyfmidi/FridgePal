<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import AppIcon from '../components/AppIcon.vue'
import AppTaskHeader from '../components/AppTaskHeader.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import CookingSheet from '../components/recipes/CookingSheet.vue'
import { fetchRecipe as apiFetchRecipe } from '../api/recipes'
import { isSeasoning, formatRecipeAmount } from '../features/recipes/unitConversion'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()

const loading = ref(true)
const loadError = ref<string | null>(null)
const recipeName = ref('')
const recipeDescription = ref('')
const baseYield = ref(2)
const multiplier = ref(1)
const ingredients = ref<{ id: string; nameKey: string; foodKey?: string; baseAmount: string; baseQuantity: number | null; baseUnit: string }[]>([])
const instructions = ref<string[]>([])
const cookOpen = ref(false)

const recipeId = computed(() => (route.query.savedId ? String(route.query.savedId) : ''))

onMounted(async () => {
  await hydrateFromServer()
  await loadRecipe()
})

async function loadRecipe() {
  loading.value = true
  loadError.value = null
  try {
    const recipe = await apiFetchRecipe(recipeId.value)
    recipeName.value = recipe.name
    recipeDescription.value = recipe.description || ''
    baseYield.value = recipe.baseYield
    multiplier.value = recipe.multiplier ?? 1
    ingredients.value = recipe.ingredients.map((ing) => {
      const match = ing.baseAmount.match(/^([0-9]+(?:\.[0-9]+)?)\s*(.*)$/)
      return {
        id: ing.id,
        nameKey: ing.nameKey,
        foodKey: ing.foodKey,
        baseAmount: ing.baseAmount,
        baseQuantity: match ? parseFloat(match[1]) : null,
        baseUnit: match ? match[2] || 'g' : 'g',
      }
    })
    instructions.value = recipe.instructions
  } catch {
    loadError.value = 'Could not load recipe.'
  } finally {
    loading.value = false
  }
}

const effectiveYield = computed(() => Math.round(baseYield.value * multiplier.value * 10) / 10)

const mainIngredients = computed(() => ingredients.value.filter((ing) => !isSeasoning(ing)))
const seasoningIngredients = computed(() => ingredients.value.filter((ing) => isSeasoning(ing)))

const cookIngredients = computed(() =>
  ingredients.value.map((ingredient) => {
    const food = inventory.value.find((f) => f.foodKey === ingredient.foodKey)
    const qty = ingredient.baseQuantity !== null
      ? Math.round(ingredient.baseQuantity * multiplier.value * 100) / 100
      : null
    return {
      id: ingredient.id,
      nameKey: ingredient.nameKey,
      foodKey: ingredient.foodKey ?? food?.foodKey,
      amount: qty !== null ? `${qty} ${ingredient.baseUnit}` : 'As needed',
    }
  }),
)

function scaledQuantity(ingredient: { baseQuantity: number | null; baseUnit: string }): string {
  if (ingredient.baseQuantity === null) return ''
  const value = Math.round(ingredient.baseQuantity * multiplier.value * 100) / 100
  return formatRecipeAmount(String(value), ingredient.baseUnit)
}

function chooseMultiplier(value: number) {
  multiplier.value = value
}

function editRecipe() {
  void router.push({ path: '/recipes/editor', query: { savedId: recipeId.value } })
}

function onCooked() {
  cookOpen.value = false
  void router.push('/')
}
</script>

<template>
  <div class="read-view">
    <AppTaskHeader :title="recipeName || t('recipeEditor.title')" :back-label="t('common.back')" @back="router.push('/recipes')">
      <template #action>
        <button type="button" class="header-edit" @click="editRecipe">
          <AppIcon name="edit" :size="17" />
          {{ t('recipeRead.edit') }}
        </button>
      </template>
    </AppTaskHeader>

    <div v-if="loading" class="read-loading">
      <p>{{ t('recipeResults.loading') }}</p>
    </div>
    <div v-else-if="loadError" class="read-error">
      <p>{{ loadError }}</p>
    </div>
    <main v-else class="read-content">
      <section class="recipe-header">
        <h1 class="recipe-header__title">{{ recipeName }}</h1>
        <p v-if="recipeDescription" class="recipe-header__desc">{{ recipeDescription }}</p>
      </section>

      <section class="portion-section">
        <div class="yield-summary">
          <div><span>{{ t('recipeEditor.recipeServes') }}</span><strong>{{ baseYield }}</strong></div>
          <div><span>{{ t('recipeEditor.thisPortion') }}</span><strong>{{ effectiveYield }}</strong></div>
        </div>
        <div class="portion-controls">
          <button type="button" :class="{ active: multiplier === 0.5 }" @click="chooseMultiplier(0.5)">{{ t('recipeEditor.half') }}</button>
          <button type="button" :class="{ active: multiplier === 1 }" @click="chooseMultiplier(1)">{{ t('recipeEditor.fullRecipe') }}</button>
          <label>
            <span>{{ t('recipeEditor.custom') }}</span>
            <input v-model.number="multiplier" type="number" min="0.1" step="0.1" :aria-label="t('recipeEditor.multiplier')">
          </label>
        </div>
      </section>

      <section class="ingredient-section">
        <h2 class="section-title">{{ t('recipeEditor.ingredients') }}</h2>
        <div class="read-ingredients">
          <div v-for="ingredient in mainIngredients" :key="ingredient.id" class="read-ingredient">
            <span class="read-ingredient__identity">
              <FoodToken
                :food-key="ingredient.foodKey"
                :name="t(ingredient.nameKey)"
                :size="38"
              />
              <span>{{ t(ingredient.nameKey) }}</span>
            </span>
            <strong class="read-ingredient__amount">{{ scaledQuantity(ingredient) || t('recipeEditor.amount') }}</strong>
          </div>
        </div>
      </section>

      <section v-if="seasoningIngredients.length" class="ingredient-section">
        <h2 class="section-title">{{ t('recipeResults.seasonings') }}</h2>
        <div class="read-seasonings">
          <span v-for="ingredient in seasoningIngredients" :key="ingredient.id" class="read-seasoning">
            <FoodToken
              :food-key="ingredient.foodKey"
              :name="t(ingredient.nameKey)"
              :size="28"
            />
            <span>{{ t(ingredient.nameKey) }}</span>
          </span>
        </div>
      </section>

      <section class="instruction-section">
        <h2 class="section-title">{{ t('recipeEditor.instructions') }}</h2>
        <ol class="read-steps">
          <li v-for="(step, index) in instructions" :key="index">
            <span class="read-steps__number">{{ index + 1 }}</span>
            <span>{{ step }}</span>
          </li>
        </ol>
      </section>

      <footer class="read-footer">
        <AppButton block @click="cookOpen = true">
          <AppIcon name="storage" :size="18" />
          {{ t('recipeRead.cookAndUpdate') }}
        </AppButton>
      </footer>
    </main>

    <CookingSheet
      :open="cookOpen"
      :recipe-name="recipeName"
      :ingredients="cookIngredients"
      :foods="inventory"
      @close="cookOpen = false"
      @cooked="onCooked"
    />
  </div>
</template>

<style scoped>
.read-view {
  width: min(100%, 880px);
  min-height: 100vh;
  padding: 0 var(--space-3) 100px;
  margin: 0 auto;
}

.header-edit {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: var(--tap-target-min);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.read-content {
  display: grid;
  gap: var(--space-6);
  padding-top: var(--space-5);
}

.recipe-header {
  display: grid;
  gap: var(--space-2);
}

.recipe-header__title {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  line-height: var(--line-height-tight);
}

.recipe-header__desc {
  color: var(--color-muted);
  font-size: var(--font-size-lg);
}

.yield-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  color: var(--color-ink);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.yield-summary > div {
  display: grid;
}

.yield-summary > div:last-child {
  text-align: right;
}

.yield-summary span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.yield-summary strong {
  font-size: var(--font-size-xl);
}

.portion-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 1.3fr;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.portion-controls button,
.portion-controls label {
  display: grid;
  min-height: 58px;
  place-items: center;
  padding: var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-weight: var(--font-weight-semibold);
}

.portion-controls button.active {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-softer);
}

.portion-controls label {
  grid-template-columns: auto 72px;
  gap: var(--space-2);
}

.portion-controls input {
  min-height: 38px;
  padding: var(--space-1) var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
}

.read-ingredients {
  display: grid;
  gap: var(--space-2);
}

.read-ingredient {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.read-ingredient__identity {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.read-ingredient__identity > span {
  font-weight: var(--font-weight-medium);
}

.read-ingredient__amount {
  font-variant-numeric: tabular-nums;
  color: var(--color-primary);
}

.read-seasonings {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.read-seasoning {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-canvas);
  box-shadow: inset 0 0 0 1px var(--color-border);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.read-steps {
  display: grid;
  gap: var(--space-4);
  list-style: none;
  padding: 0;
}

.read-steps li {
  display: grid;
  grid-template-columns: 30px 1fr;
  align-items: start;
  gap: var(--space-3);
}

.read-steps__number {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: var(--radius-full);
  color: var(--color-primary-hover);
  background: var(--color-primary-soft);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.read-footer {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.read-loading,
.read-error {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-5);
  border-radius: var(--radius-card);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  text-align: center;
  place-items: center;
}

@media (max-width: 520px) {
  .portion-controls {
    grid-template-columns: 1fr 1fr;
  }

  .portion-controls label {
    grid-column: 1 / -1;
  }
}
</style>
