import { computed, ref, type Ref } from 'vue'
import type { InventoryFood } from '../storage/inventory'

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

export function useRescueStore(inventory: Ref<InventoryFood[]>) {
  const selectedFoods = computed(() => {
    const byId = new Map(inventory.value.map((food) => [food.id, food]))
    return selectedIds.value.map((id) => byId.get(id)).filter((food): food is InventoryFood => food !== undefined)
  })

  return {
    selectedIds,
    selectedFoods,
    isAtCapacity: computed(() => selectedIds.value.length >= 7),
    toggleFood,
    removeFood,
  }
}
