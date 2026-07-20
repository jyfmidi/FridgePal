export interface RescueSource {
  id: string
  url: string
  title: string
  publisher: string
  domain: string
  retrievedAt: string
  baseYield: number | null
  usedFoodKeys: string[]
}

export interface PlanIngredient {
  originalText: string
  amountKind: string
  amount: string | null
  unit: string | null
  mappingSuggestion: string | null
  provenance: string
  needsReview: boolean
}

export interface AiPlan {
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
  sources: RescueSource[]
  aiPlan: AiPlan | null
  aiPlanError: string | null
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
): Promise<SearchResponse> {
  const response = await fetch('/api/rescue/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selectedFoods, servings, locale }),
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
  sources: RescueSource[]
  aiPlan: AiPlan | null
  aiPlanError: string | null
  createdAt: string
  searchedAt: string | null
}

export async function fetchRescueSession(sessionId: string): Promise<RescueSession> {
  const response = await fetch(`/api/rescue/${encodeURIComponent(sessionId)}`)
  if (!response.ok) throw new Error(`Rescue session fetch failed with status ${response.status}`)
  return response.json() as Promise<RescueSession>
}
