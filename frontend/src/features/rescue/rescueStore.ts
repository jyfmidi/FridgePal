import { computed, ref, type Ref } from 'vue'
import type { InventoryFood } from '../storage/inventory'
import { searchRecipes, type SearchResponse } from '../../api/rescue'

const RESCUE_KEY = 'fridgital.rescue.selection.v1'
const DEFAULT_SELECTION = [
  'chicken-breast-FRIDGE',
  'spinach-FRIDGE',
  'mushrooms-FRIDGE',
  'broccoli-FRIDGE',
  'tofu-FRIDGE',
]

function loadSelection(): string[] {
  try {
    const saved = localStorage.getItem(RESCUE_KEY)
    if (saved) return (JSON.parse(saved) as string[]).slice(0, 7)
  } catch {
    // Invalid browser data falls back to the deterministic fixture selection.
  }
  return [...DEFAULT_SELECTION]
}

const selectedIds = ref<string[]>(loadSelection())

function persist() {
  localStorage.setItem(RESCUE_KEY, JSON.stringify(selectedIds.value))
}

function syncSelectionAgainstInventory(inventory: Ref<InventoryFood[]>) {
  const validIds = new Set(inventory.value.map((food) => food.id))
  const before = selectedIds.value.length
  selectedIds.value = selectedIds.value.filter((id) => validIds.has(id))
  if (selectedIds.value.length !== before) persist()
}

function toggleFood(foodId: string): boolean {
  const existingIndex = selectedIds.value.indexOf(foodId)
  if (existingIndex >= 0) {
    selectedIds.value.splice(existingIndex, 1)
    persist()
    return true
  }
  if (selectedIds.value.length >= 7) return false
  selectedIds.value.push(foodId)
  persist()
  return true
}

function removeFood(foodId: string) {
  const index = selectedIds.value.indexOf(foodId)
  if (index >= 0) {
    selectedIds.value.splice(index, 1)
    persist()
  }
}

function replaceSelection(foodIds: string[]) {
  selectedIds.value = [...new Set(foodIds)].slice(0, 7)
  persist()
}

const searchResult = ref<SearchResponse | null>(null)
const searching = ref(false)
const searchError = ref<string | null>(null)
const searchCompleted = ref(false)
const latestSessionId = ref<string | null>(null)
const newMealIdea = ref(false)

function clearSearch() {
  searchResult.value = null
  searchError.value = null
}

function clearNewMealIdea() {
  newMealIdea.value = false
}

export function useRescueStore(inventory: Ref<InventoryFood[]>) {
  syncSelectionAgainstInventory(inventory)

  const selectedFoods = computed(() => {
    const byId = new Map(inventory.value.map((food) => [food.id, food]))
    return selectedIds.value.map((id) => byId.get(id)).filter((food): food is InventoryFood => food !== undefined)
  })

  async function performSearch(locale: string = 'en', cuisine: string = '') {
    searching.value = true
    searchError.value = null
    try {
      const inputs = selectedFoods.value.map((food) => ({
        foodKey: food.foodKey,
        names: food.names ?? { en: food.nameKey },
        quantity: String(food.quantity),
        unit: food.unit,
        location: food.location.toUpperCase(),
        urgency: food.urgency,
      }))
      searchResult.value = await searchRecipes(inputs, 2, locale, cuisine)
      searchCompleted.value = true
      latestSessionId.value = searchResult.value?.sessionId ?? null
      newMealIdea.value = true
    } catch {
      searchResult.value = null
      searchError.value = 'search_failed'
    } finally {
      searching.value = false
    }
  }

  return {
    selectedIds,
    selectedFoods,
    selectionCount: computed(() => selectedFoods.value.length),
    isAtCapacity: computed(() => selectedFoods.value.length >= 7),
    toggleFood,
    removeFood,
    replaceSelection,
    searchResult,
    searching,
    searchError,
    searchCompleted,
    latestSessionId,
    newMealIdea,
    performSearch,
    clearSearch,
    clearNewMealIdea,
  }
}
