export interface SavedRecipeIngredient {
  id: string
  nameKey: string
  foodKey?: string
  baseAmount: string
}

export interface SavedRecipe {
  id: string
  name: string
  description: string | null
  baseYield: number
  multiplier: number
  ingredients: SavedRecipeIngredient[]
  instructions: string[]
  originType: string
  originId: string | null
  sourceUrl: string | null
  sourcePublisher: string | null
  lastCookedPortion: number | null
  createdAt: string
  updatedAt: string
}

export interface SaveRecipeInput {
  id?: string
  name: string
  description?: string | null
  baseYield: number
  multiplier: number
  ingredients: SavedRecipeIngredient[]
  instructions: string[]
  originType?: string
  originId?: string | null
  sourceUrl?: string | null
  sourcePublisher?: string | null
}

export interface SaveRecipeResponse {
  id: string
  created: boolean
}

export async function fetchRecipes(): Promise<SavedRecipe[]> {
  const response = await fetch('/api/recipes')
  if (!response.ok) throw new Error(`Recipes fetch failed with status ${response.status}`)
  const body = await response.json() as { recipes: SavedRecipe[] }
  return body.recipes
}

export async function fetchRecipe(id: string): Promise<SavedRecipe> {
  const response = await fetch(`/api/recipes/${encodeURIComponent(id)}`)
  if (!response.ok) throw new Error(`Recipe fetch failed with status ${response.status}`)
  return response.json() as Promise<SavedRecipe>
}

export async function saveRecipe(input: SaveRecipeInput): Promise<SaveRecipeResponse> {
  const response = await fetch('/api/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw new Error(`Recipe save failed with status ${response.status}`)
  return response.json() as Promise<SaveRecipeResponse>
}

export async function updateRecipe(id: string, input: SaveRecipeInput): Promise<SaveRecipeResponse> {
  const response = await fetch(`/api/recipes/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw new Error(`Recipe update failed with status ${response.status}`)
  return response.json() as Promise<SaveRecipeResponse>
}
