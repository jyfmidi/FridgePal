import { computed, ref } from 'vue'

const SAVED_RECIPES_KEY = 'fridgital.saved-recipes.v1'

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

export interface SavedRecipe extends RecipeDraftData {
  id: string
  originType: 'ai-plan' | 'source' | 'personal'
  originId: string
  sourceUrl?: string
  sourcePublisher?: string
  savedAt: string
  lastCookedPortion?: number
}

const demoRecipes: SavedRecipe[] = [
  {
    id: 'saved-demo-penne',
    originType: 'source',
    originId: 'creamy-spinach-mushroom-penne',
    sourceUrl: 'https://www.bbcgoodfood.com/recipes/creamy-spinach-mushroom-penne',
    sourcePublisher: 'Good Food',
    name: 'Creamy spinach & mushroom penne',
    description: 'A fast, creamy pasta built around mushrooms and leafy greens.',
    baseYield: 2,
    multiplier: 1,
    ingredients: [
      { id: 'spinach-FRIDGE', nameKey: 'foods.spinach', foodKey: 'spinach', baseAmount: '200 g' },
      { id: 'mushrooms-FRIDGE', nameKey: 'foods.mushrooms', foodKey: 'mushrooms', baseAmount: '120 g' },
      { id: 'pasta-PANTRY', nameKey: 'foods.pasta', foodKey: 'pasta', baseAmount: '175 g' },
      { id: 'garlic-PANTRY', nameKey: 'foods.garlic', foodKey: 'garlic', baseAmount: '10 g' },
    ],
    instructions: ['Cook the pasta until just tender.', 'Sauté the mushrooms and garlic.', 'Fold in spinach, pasta, and the creamy sauce.'],
    savedAt: '2026-07-17T09:30:00.000Z',
    lastCookedPortion: 1,
  },
  {
    id: 'saved-demo-skillet',
    originType: 'ai-plan',
    originId: 'ai-plan',
    name: 'Flexible rescue skillet',
    description: 'A one-pan dinner designed around foods that need using soon.',
    baseYield: 2,
    multiplier: 1,
    ingredients: [
      { id: 'chicken-breast-FRIDGE', nameKey: 'foods.chickenBreast', foodKey: 'chicken-breast', baseAmount: '300 g' },
      { id: 'broccoli-FRIDGE', nameKey: 'foods.broccoli', foodKey: 'broccoli', baseAmount: '200 g' },
      { id: 'mushrooms-FRIDGE', nameKey: 'foods.mushrooms', foodKey: 'mushrooms', baseAmount: '180 g' },
      { id: 'spinach-FRIDGE', nameKey: 'foods.spinach', foodKey: 'spinach', baseAmount: '120 g' },
    ],
    instructions: ['Prep the selected foods.', 'Cook proteins and firm vegetables.', 'Fold in greens and season.'],
    savedAt: '2026-07-16T18:15:00.000Z',
  },
]

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

function loadRecipes(): SavedRecipe[] {
  try {
    const saved = localStorage.getItem(SAVED_RECIPES_KEY)
    if (saved) return (JSON.parse(saved) as SavedRecipe[]).map(normalizeRecipeDraftData)
  } catch {
    // Malformed browser data falls back to deterministic demo recipes.
  }
  return demoRecipes.map(normalizeRecipeDraftData)
}

const savedRecipes = ref<SavedRecipe[]>(loadRecipes())

function persist() {
  localStorage.setItem(SAVED_RECIPES_KEY, JSON.stringify(savedRecipes.value))
}

function getSavedRecipe(recipeId: string | undefined): SavedRecipe | undefined {
  if (!recipeId) return undefined
  return savedRecipes.value.find((recipe) => recipe.id === recipeId)
}

function saveRecipe(input: {
  id?: string
  originType: SavedRecipe['originType']
  originId: string
  sourceUrl?: string
  sourcePublisher?: string
  draft: RecipeDraftData
}): SavedRecipe {
  const existing = getSavedRecipe(input.id)
  const recipe: SavedRecipe = {
    ...input.draft,
    id: existing?.id ?? crypto.randomUUID(),
    originType: input.originType,
    originId: input.originId,
    sourceUrl: input.sourceUrl,
    sourcePublisher: input.sourcePublisher,
    savedAt: new Date().toISOString(),
    lastCookedPortion: existing?.lastCookedPortion,
  }

  const existingIndex = savedRecipes.value.findIndex((item) => item.id === recipe.id)
  if (existingIndex >= 0) savedRecipes.value.splice(existingIndex, 1, recipe)
  else savedRecipes.value.unshift(recipe)
  persist()
  return recipe
}

export function useRecipeStore() {
  return {
    savedRecipes,
    savedCount: computed(() => savedRecipes.value.length),
    getSavedRecipe,
    saveRecipe,
  }
}
