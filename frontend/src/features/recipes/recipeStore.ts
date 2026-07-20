import { computed, ref } from 'vue'
import { fetchRecipes, saveRecipe as apiSaveRecipe, updateRecipe as apiUpdateRecipe, type SavedRecipe, type SaveRecipeInput } from '../../api/recipes'

export interface RecipeIngredientDraft {
  id: string
  nameKey: string
  foodKey?: string
  baseAmount: string
}

export interface RecipeDraftData {
  name: string
  description: string
  baseYield: number
  multiplier: number
  ingredients: RecipeIngredientDraft[]
  instructions: string[]
}

export type { SavedRecipe }

const savedRecipes = ref<SavedRecipe[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function hydrateFromServer() {
  loading.value = true
  error.value = null
  try {
    savedRecipes.value = await fetchRecipes()
  } catch {
    error.value = 'Failed to load recipes'
  } finally {
    loading.value = false
  }
}

function getSavedRecipe(recipeId: string | undefined): SavedRecipe | undefined {
  if (!recipeId) return undefined
  return savedRecipes.value.find((recipe) => recipe.id === recipeId)
}

async function saveRecipe(input: {
  id?: string
  originType: string
  originId: string
  sourceUrl?: string
  sourcePublisher?: string
  draft: RecipeDraftData
}): Promise<SavedRecipe> {
  const payload: SaveRecipeInput = {
    id: input.id,
    name: input.draft.name,
    description: input.draft.description || null,
    baseYield: input.draft.baseYield,
    multiplier: input.draft.multiplier,
    ingredients: input.draft.ingredients,
    instructions: input.draft.instructions,
    originType: input.originType,
    originId: input.originId,
    sourceUrl: input.sourceUrl,
    sourcePublisher: input.sourcePublisher,
  }
  const response = input.id
    ? await apiUpdateRecipe(input.id, payload)
    : await apiSaveRecipe(payload)
  // After save, refresh the list to get the updated recipe
  await hydrateFromServer()
  const saved = getSavedRecipe(response.id)
  return saved ?? savedRecipes.value[0]!
}

export function useRecipeStore() {
  return {
    savedRecipes,
    savedCount: computed(() => savedRecipes.value.length),
    loading,
    error,
    getSavedRecipe,
    saveRecipe,
    hydrateFromServer,
  }
}

/** One-time compatibility cleanup for the old deterministic garlic fixture. */
export function normalizeRecipeDraftData<T extends RecipeDraftData>(draft: T): T {
  return {
    ...draft,
    ingredients: draft.ingredients.map((ingredient) => ({
      ...ingredient,
      baseAmount: ingredient.foodKey === 'garlic' && ingredient.baseAmount.trim().toLowerCase() === '2 cloves'
        ? '10 g'
        : ingredient.baseAmount,
    })),
  }
}
