import { computed, ref } from 'vue'
import { fetchFoodLibrary, type LibraryFood } from '../../api/library'
import { registerCustomIcon, registerVisualKey } from '../../components/food-token'
import { foodCatalog, type FoodCatalogItem, type InventoryUnit, type StorageLocation } from './inventory'

/**
 * Server-owned Food Library (admin-managed) merged with the built-in static
 * catalog. The server is the source of truth: an admin-created or admin-edited
 * food replaces its static twin, and foods removed by the admin disappear
 * from Add Food suggestions.
 */
const serverFoods = ref<LibraryFood[]>([])
let loaded = false
let sharedLoad: Promise<void> | null = null

function toCatalogItem(food: LibraryFood): FoodCatalogItem {
  const rule = food.shelfLife.find((item) => item.storageLocation === food.recommendedStorage)
  return {
    foodKey: food.foodKey,
    // Foods without a static twin get their names at runtime (i18n merge) and
    // render through `names` directly in Add Food.
    nameKey: undefined,
    names: { en: food.names.en, 'zh-CN': food.names['zh-CN'] ?? food.names.en },
    defaultLocation: food.recommendedStorage.toLowerCase() as StorageLocation,
    defaultQuantity: 1,
    defaultUnit: food.baseUnit as InventoryUnit,
    visualKey: food.visualKey,
    aliases: food.aliases,
    packagePresets: food.packagePresets.map((preset) => ({
      label: preset.label,
      amount: Number(preset.amount),
      unit: preset.unit as InventoryUnit,
    })),
    shelfLifeDays: rule?.durationDays,
  }
}

export function useFoodLibrary() {
  async function hydrateLibrary(force = false): Promise<void> {
    if (loaded && !force) return
    if (!sharedLoad) {
      sharedLoad = fetchFoodLibrary()
        .then((foods) => {
          serverFoods.value = foods
          for (const food of foods) {
            registerVisualKey(food.foodKey, food.visualKey)
            if (food.customIcon) {
              registerCustomIcon(food.foodKey, food.customIcon)
            }
          }
        })
        .catch(() => {
          // Library is a progressive enhancement; Add Food falls back to the
          // built-in catalog when the server is unreachable.
        })
        .finally(() => {
          sharedLoad = null
          loaded = true
        })
    }
    return sharedLoad
  }

  /** Built-in catalog overlaid with server truth, preserving static order. */
  const catalog = computed<FoodCatalogItem[]>(() => {
    const byKey = new Map<string, FoodCatalogItem>()
    for (const item of foodCatalog) byKey.set(item.foodKey, item)
    for (const food of serverFoods.value) byKey.set(food.foodKey, toCatalogItem(food))
    return [...byKey.values()]
  })

  return { catalog, hydrateLibrary, loaded }
}
