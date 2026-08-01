import { apiFetch } from './client'
export interface PlanIngredient {
  originalText: string
  amountKind: string
  amount: string | null
  unit: string | null
  mappingSuggestion: string | null
  provenance: string
  needsReview: boolean
}

export interface Recipe {
  title: string
  description: string | null
  baseYield: number
  ingredients: PlanIngredient[]
  steps: string[]
  sourceUrls: string[]
  analysisStatus: string
  warnings: string[]
}

export interface SearchResponse {
  sessionId: string
  recipes: Recipe[]
  recipeErrors: string[]
}

export interface SelectedFoodInput {
  foodKey: string
  names: Record<string, string>
  quantity: string
  unit: string
  location: string
  urgency: string
}

export async function searchRecipes(
  selectedFoods: SelectedFoodInput[],
  servings: number,
  locale: string,
  cuisine: string,
): Promise<SearchResponse> {
  const response = await apiFetch('/api/rescue/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ selectedFoods, servings, locale, cuisine }),
  })
  if (!response.ok) {
    throw new Error(`Recipe search failed with status ${response.status}`)
  }
  return response.json() as Promise<SearchResponse>
}

export interface RescueSession {
  sessionId: string
  status: string
  selectedFoods: SelectedFoodInput[]
  servings: number
  locale: string
  cuisine?: string
  recipes: Recipe[]
  recipeErrors: string[]
  createdAt: string
  searchedAt: string | null
}

export async function fetchRescueSession(sessionId: string): Promise<RescueSession> {
  const response = await apiFetch(`/api/rescue/${encodeURIComponent(sessionId)}`, { credentials: 'include' })
  if (!response.ok) throw new Error(`Rescue session fetch failed with status ${response.status}`)
  return response.json() as Promise<RescueSession>
}

export async function fetchMealIdeaHistory(limit: number = 3): Promise<RescueSession[]> {
  const response = await apiFetch(`/api/rescue/sessions?limit=${limit}`, { credentials: 'include' })
  if (!response.ok) throw new Error(`Meal idea history fetch failed with status ${response.status}`)
  const body = await response.json() as { sessions: RescueSession[] }
  return body.sessions
}
