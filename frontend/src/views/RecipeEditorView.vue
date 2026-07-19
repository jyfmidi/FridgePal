<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import AppButton from '../components/AppButton.vue'
import FoodToken from '../components/food-token/FoodToken.vue'
import CookingSheet from '../components/recipes/CookingSheet.vue'
import StorageIngredientPicker from '../components/recipes/StorageIngredientPicker.vue'
import { buildPlanIngredients, recipeSources } from '../features/recipes/fixtures'
import { useRecipeStore, type RecipeDraftData, type RecipeIngredientDraft } from '../features/recipes/recipeStore'
import { useRescueStore } from '../features/rescue/rescueStore'
import { useInventoryStore } from '../features/storage/inventoryStore'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { inventory, hydrateFromServer } = useInventoryStore()
const { selectedFoods } = useRescueStore(inventory)
const { getSavedRecipe, saveRecipe } = useRecipeStore()
const origin = computed(() => String(route.query.origin ?? 'ai-plan'))
const routeSavedId = computed(() => (route.query.savedId ? String(route.query.savedId) : undefined))
const openedSavedRecipe = computed(() => getSavedRecipe(routeSavedId.value))
const source = computed(() => recipeSources.find((item) => item.id === origin.value))
const draftKey = computed(() => `fridgital.recipe.draft.v1.${origin.value}`)

function defaultDraft(): RecipeDraftData {
  if (openedSavedRecipe.value) {
    return {
      name: openedSavedRecipe.value.name,
      description: openedSavedRecipe.value.description,
      baseYield: openedSavedRecipe.value.baseYield,
      multiplier: openedSavedRecipe.value.multiplier,
      ingredients: openedSavedRecipe.value.ingredients.map((ingredient) => ({ ...ingredient })),
      instructions: [...openedSavedRecipe.value.instructions],
    }
  }
  return {
    name: source.value?.title ?? t('recipeResults.aiTitle'),
    description: source.value
      ? t('recipeResults.sourcesHint')
      : t('recipeResults.aiDescription'),
    baseYield: source.value?.serves ?? 2,
    multiplier: 1,
    ingredients: buildPlanIngredients(selectedFoods.value).map((ingredient) => ({
      id: ingredient.id,
      nameKey: ingredient.nameKey,
      foodKey: inventory.value.find((food) => food.id === ingredient.id)?.foodKey,
      baseAmount: ingredient.amount,
    })),
    instructions: [t('recipeResults.stepOne'), t('recipeResults.stepTwo'), t('recipeResults.stepThree')],
  }
}

function loadDraft(): RecipeDraftData {
  if (openedSavedRecipe.value) return defaultDraft()
  try {
    const saved = localStorage.getItem(draftKey.value)
    if (saved) return JSON.parse(saved) as RecipeDraftData
  } catch {
    // A malformed local draft falls back to a clean normalized fixture draft.
  }
  return defaultDraft()
}

const initial = loadDraft()
const name = ref(initial.name)
const description = ref(initial.description)
const baseYield = ref(initial.baseYield)
const multiplier = ref(initial.multiplier)
const ingredients = ref<RecipeIngredientDraft[]>(initial.ingredients)
const instructions = ref<string[]>(initial.instructions)
const pickerOpen = ref(false)
const addStorageButton = ref<HTMLButtonElement | null>(null)
const draftSaved = ref(false)
const recipeSaved = ref(Boolean(openedSavedRecipe.value))
const savedRecipeId = ref(openedSavedRecipe.value?.id)
const cookOpen = ref(false)
const notice = ref('')
let noticeTimer: ReturnType<typeof setTimeout> | undefined

function showNotice(message: string) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => (notice.value = ''), 2500)
}

const effectiveYield = computed(() => Math.round(baseYield.value * multiplier.value * 10) / 10)
const ingredientIds = computed(() => new Set(ingredients.value.map((ingredient) => ingredient.id)))
const inventoryById = computed(() => new Map(inventory.value.map((food) => [food.id, food])))
/** Recipe ingredients with effective (portion-scaled) amounts, resolved against Storage. */
const cookIngredients = computed(() =>
  ingredients.value.map((ingredient) => ({
    id: ingredient.id,
    nameKey: ingredient.nameKey,
    foodKey: ingredient.foodKey ?? inventoryById.value.get(ingredient.id)?.foodKey,
    amount: scaledAmount(ingredient.baseAmount),
  })),
)

onMounted(() => {
  void hydrateFromServer()
})

function scaledAmount(baseAmount: string): string {
  const match = baseAmount.match(/^([0-9]+(?:\.[0-9]+)?)(.*)$/)
  if (!match) return baseAmount
  const value = Math.round(Number(match[1]) * multiplier.value * 100) / 100
  return `${value}${match[2]}`
}

function updateEffectiveAmount(index: number, effectiveAmount: string) {
  const match = effectiveAmount.match(/^([0-9]+(?:\.[0-9]+)?)(.*)$/)
  ingredients.value[index]!.baseAmount = match
    ? `${Math.round((Number(match[1]) / multiplier.value) * 100) / 100}${match[2]}`
    : effectiveAmount
  markDirty()
}

function chooseMultiplier(value: number) {
  multiplier.value = value
  markDirty()
}

function addIngredient(foodId: string) {
  if (ingredientIds.value.has(foodId)) return
  const food = inventory.value.find((item) => item.id === foodId)
  if (!food) return
  ingredients.value.push({ id: food.id, nameKey: food.nameKey, foodKey: food.foodKey, baseAmount: 'As needed' })
  markDirty()
}

function addIngredients(foodIds: string[]) {
  foodIds.forEach(addIngredient)
  closePicker()
}

function closePicker() {
  pickerOpen.value = false
  void nextTick(() => addStorageButton.value?.focus())
}

function ingredientFood(foodId: string) {
  return inventoryById.value.get(foodId)
}

function markDirty() {
  draftSaved.value = false
  recipeSaved.value = false
}

function currentDraft(): RecipeDraftData {
  return {
    name: name.value,
    description: description.value,
    baseYield: baseYield.value,
    multiplier: multiplier.value,
    ingredients: ingredients.value,
    instructions: instructions.value,
  }
}

function saveDraft() {
  const draft = currentDraft()
  localStorage.setItem(draftKey.value, JSON.stringify(draft))
  draftSaved.value = true
}

function saveToRecipes() {
  const stored = saveRecipe({
    id: savedRecipeId.value,
    originType: source.value ? 'source' : 'ai-plan',
    originId: origin.value,
    sourceUrl: source.value?.url,
    sourcePublisher: source.value?.publisher,
    draft: currentDraft(),
  })
  savedRecipeId.value = stored.id
  draftSaved.value = true
  recipeSaved.value = true
  localStorage.setItem(draftKey.value, JSON.stringify(currentDraft()))
  void router.replace({ query: { ...route.query, savedId: stored.id } })
}

function startCooking() {
  // FR-RCP-001: an unsaved draft is auto-saved through the normal save path
  // before reconciliation opens, with no extra prompt.
  if (!recipeSaved.value) saveToRecipes()
  cookOpen.value = true
}

function onCooked() {
  cookOpen.value = false
  void hydrateFromServer()
  showNotice(t('cooking.updated'))
}
</script>

<template>
  <div class="editor-view">
    <header class="editor-header">
      <button type="button" :aria-label="t('common.back')" @click="router.back()">←</button>
      <strong>{{ t('recipeEditor.title') }}</strong>
      <span>{{ t(recipeSaved ? 'recipeEditor.saved' : draftSaved ? 'recipeEditor.draftSaved' : 'recipeEditor.draft') }}</span>
    </header>

    <div v-if="notice" class="notice" role="status">
      <span>{{ notice }}</span>
      <button type="button" :aria-label="t('storageItem.dismiss')" @click="notice = ''">×</button>
    </div>

    <main class="editor-content">
      <section class="provenance">
        <div>
          <span>{{ t('recipeEditor.provenance') }}</span>
          <strong>{{ source ? source.publisher : t('recipeEditor.aiProvenance', { count: recipeSources.length }) }}</strong>
        </div>
        <a v-if="source" :href="source.url" target="_blank" rel="noopener noreferrer">{{ t('recipeResults.openSource') }} ↗</a>
      </section>

      <section class="identity-fields">
        <label>
          <span>{{ t('recipeEditor.name') }}</span>
          <input v-model="name" @input="markDirty">
        </label>
        <label>
          <span>{{ t('recipeEditor.description') }}</span>
          <textarea v-model="description" rows="3" @input="markDirty" />
        </label>
      </section>

      <section class="portion-section">
        <div class="yield-summary">
          <div><span>{{ t('recipeEditor.originalYield') }}</span><strong>{{ baseYield }}</strong></div>
          <div><span>{{ t('recipeEditor.effectiveYield') }}</span><strong>{{ effectiveYield }}</strong></div>
        </div>
        <h2>{{ t('recipeEditor.portions') }}</h2>
        <div class="portion-controls">
          <button type="button" :class="{ active: multiplier === 0.5 }" @click="chooseMultiplier(0.5)">{{ t('recipeEditor.half') }}</button>
          <button type="button" :class="{ active: multiplier === 1 }" @click="chooseMultiplier(1)">{{ t('recipeEditor.original') }}</button>
          <label>
            <span>{{ t('recipeEditor.custom') }}</span>
            <input v-model.number="multiplier" type="number" min="0.1" step="0.1" :aria-label="t('recipeEditor.multiplier')" @input="markDirty">
          </label>
        </div>
      </section>

      <section class="ingredient-section">
        <h2>{{ t('recipeEditor.ingredients') }}</h2>
        <div class="editor-ingredients stagger-in">
          <label v-for="(ingredient, index) in ingredients" :key="ingredient.id">
            <span class="ingredient-identity">
              <FoodToken
                :food-key="ingredientFood(ingredient.id)?.foodKey"
                :name="t(ingredient.nameKey)"
                :size="38"
              />
              <span>{{ t(ingredient.nameKey) }}</span>
            </span>
            <input :value="scaledAmount(ingredient.baseAmount)" :aria-label="`${t(ingredient.nameKey)} ${t('recipeEditor.amount')}`" @input="updateEffectiveAmount(index, ($event.target as HTMLInputElement).value)">
          </label>
          <button ref="addStorageButton" class="add-storage-tile" type="button" @click="pickerOpen = true">
            <span aria-hidden="true">＋</span>
            {{ t('recipeEditor.addFromStorage') }}
          </button>
        </div>
      </section>

      <section class="instruction-section">
        <h2>{{ t('recipeEditor.instructions') }}</h2>
        <label v-for="(_, index) in instructions" :key="index">
          <span>{{ index + 1 }}</span>
          <textarea v-model="instructions[index]" rows="3" @input="markDirty" />
        </label>
      </section>

      <footer class="editor-footer sheet-up">
        <p>{{ recipeSaved ? t('recipeEditor.savedToRecipes') : draftSaved ? t('recipeEditor.savedNotice') : t('recipeEditor.saveHint') }}</p>
        <div class="editor-footer__actions">
          <AppButton variant="secondary" :disabled="name.trim().length === 0" @click="saveDraft">{{ t('recipeEditor.saveDraft') }}</AppButton>
          <AppButton variant="secondary" :disabled="name.trim().length === 0" @click="saveToRecipes">
            {{ t(savedRecipeId ? 'recipeEditor.saveChanges' : 'recipeEditor.saveRecipe') }}
          </AppButton>
          <AppButton class="editor-footer__cook" :disabled="name.trim().length === 0" @click="startCooking">
            {{ t('recipeEditor.cookThis') }}
          </AppButton>
        </div>
      </footer>
    </main>

    <StorageIngredientPicker
      :open="pickerOpen"
      :foods="inventory"
      :ingredient-ids="ingredientIds"
      @close="closePicker"
      @confirm="addIngredients"
    />

    <CookingSheet
      :open="cookOpen"
      :recipe-name="name"
      :ingredients="cookIngredients"
      :foods="inventory"
      @close="cookOpen = false"
      @cooked="onCooked"
    />
  </div>
</template>

<style scoped>
.editor-view {
  width: min(100%, 880px);
  min-height: 100vh;
  padding: 0 var(--space-3) 100px;
  margin: 0 auto;
}

.editor-header {
  position: sticky;
  z-index: var(--z-sticky);
  top: 0;
  display: grid;
  min-height: 64px;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding-top: var(--safe-area-top);
  background: var(--color-header-bg);
  border-bottom: 1px solid var(--color-border);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
}

.editor-header button {
  min-height: var(--tap-target-min);
  justify-self: start;
  color: var(--color-primary);
  font-size: var(--font-size-xl);
}

.editor-header span {
  justify-self: end;
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.editor-content {
  display: grid;
  gap: var(--space-6);
  padding-top: var(--space-5);
}

.provenance,
.yield-summary,
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.provenance {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-primary-softer);
}

.provenance > div,
.yield-summary > div {
  display: grid;
}

.provenance span,
.yield-summary span,
.identity-fields label > span,
.ingredient-identity > span {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.identity-fields,
.portion-section,
.ingredient-section,
.instruction-section {
  display: grid;
  gap: var(--space-3);
}

.identity-fields label {
  display: grid;
  gap: var(--space-1);
}

input,
textarea {
  width: 100%;
  min-height: var(--tap-target-min);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

textarea {
  resize: vertical;
}

.identity-fields input {
  min-height: 54px;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.yield-summary {
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  background: var(--color-rail);
  color: var(--color-on-rail);
}

.yield-summary > div:last-child {
  text-align: right;
}

.yield-summary span {
  color: var(--color-on-rail-muted);
}

.yield-summary strong {
  font-size: var(--font-size-xl);
}

.portion-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 1.3fr;
  gap: var(--space-2);
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
}

.editor-ingredients {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.editor-ingredients label {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
}

.ingredient-identity {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--space-2);
}

.ingredient-identity > span {
  overflow: hidden;
  color: var(--color-ink);
  font-weight: var(--font-weight-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.add-storage-tile {
  display: flex;
  min-height: 96px;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px dashed var(--color-primary);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
}

.instruction-section label {
  display: grid;
  grid-template-columns: 30px 1fr;
  align-items: start;
  gap: var(--space-2);
}

.instruction-section label > span {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: var(--radius-full);
  color: var(--color-on-rail);
  background: var(--color-rail);
  font-size: var(--font-size-sm);
}

.editor-footer {
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.editor-footer p {
  color: var(--color-muted);
  font-size: var(--font-size-sm);
}

.editor-footer__actions {
  display: flex;
  gap: var(--space-2);
}

.notice {
  position: sticky;
  z-index: var(--z-sticky);
  top: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-on-primary);
  background: var(--color-primary);
  box-shadow: var(--shadow-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.notice button {
  min-width: var(--tap-target-min);
  min-height: var(--tap-target-min);
  font-size: 1.1rem;
}

@media (max-width: 520px) {
  .provenance,
  .editor-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .editor-footer__actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .editor-footer__cook {
    grid-column: 1 / -1;
  }

  .portion-controls {
    grid-template-columns: 1fr 1fr;
  }

  .portion-controls label {
    grid-column: 1 / -1;
  }
}
</style>
