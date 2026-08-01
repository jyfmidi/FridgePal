import { computed, ref } from 'vue'
import { fetchStorage, patchLot, persistCheckIn, reduceInventory, discardLot, type ApiLocation, type PatchLotInput, type StorageApiItem } from '../../api/inventory'
import { i18n } from '../../i18n'
import { registerCustomIcon, registerVisualKey } from '../../components/food-token'
import {
  convertInventoryQuantity,
  demoInventory,
  foodCatalog,
  isInventoryUnit,
  normalizeLegacyInventoryUnit,
  roundInventoryQuantity,
  type InventoryFood,
  type InventoryUnit,
  type StorageLocation,
  type Urgency,
} from './inventory'

const STORAGE_KEY = 'fridgital.inventory.v1'

/**
 * Custom foods have no catalog entry, so their display names are registered
 * into the i18n catalogs at runtime under `foods.<foodKey>`; every view keeps
 * resolving names through the existing `t(food.nameKey)` path.
 */
export function registerCustomFoodNames(foodKey: string, names: { en: string; 'zh-CN'?: string }): string {
  i18n.global.mergeLocaleMessage('en', { foods: { [foodKey]: names.en } })
  i18n.global.mergeLocaleMessage('zh-CN', { foods: { [foodKey]: names['zh-CN'] ?? names.en } })
  return `foods.${foodKey}`
}

function loadInventory(): InventoryFood[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const foods = JSON.parse(saved) as InventoryFood[]
      for (const food of foods) {
        food.unit = normalizeLegacyInventoryUnit(food.unit)
        if (food.names && !foodCatalog.some((catalogItem) => catalogItem.nameKey === food.nameKey)) {
          registerCustomFoodNames(food.foodKey, food.names)
        }
      }
      return foods
    }
  } catch {
    // A blocked/corrupt local store falls back to the deterministic demo inventory.
  }
  return structuredClone(demoInventory)
}

const inventory = ref<InventoryFood[]>(loadInventory())
const syncState = ref<'checking' | 'synced' | 'local-only'>('checking')

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(inventory.value))
}

function urgencyFromDate(expiresOn?: string): Urgency {
  if (!expiresOn) return 'neutral'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expiry = new Date(`${expiresOn}T00:00:00`)
  const days = Math.round((expiry.getTime() - today.getTime()) / 86_400_000)
  if (days < 0) return 'past'
  if (days === 0) return 'today'
  if (days <= 2) return 'soon'
  if (days <= 5) return 'later'
  return 'neutral'
}

const urgencyRank: Record<Urgency, number> = {
  past: 5,
  today: 4,
  soon: 3,
  later: 2,
  neutral: 1,
}

export interface CheckInInput {
  foodKey: string
  /** Catalog i18n key; omitted for custom foods, whose names are registered at runtime. */
  nameKey?: string
  names: { en: string; 'zh-CN': string }
  quantity: number
  unit: InventoryUnit
  location: StorageLocation
  storedOn: string
  expiresOn?: string
}

function checkInLocally(input: CheckInInput) {
  const existingDefinition = inventory.value.find((food) => food.foodKey === input.foodKey)
  const baseUnit = existingDefinition && isInventoryUnit(existingDefinition.unit) ? existingDefinition.unit : input.unit
  const storedQuantity = roundInventoryQuantity(convertInventoryQuantity(input.quantity, input.unit, baseUnit))
  const existing = inventory.value.find(
    (food) => food.foodKey === input.foodKey && food.location === input.location,
  )

  if (existing) {
    existing.quantity = roundInventoryQuantity(existing.quantity + storedQuantity)
    existing.unit = baseUnit
    const incomingUrgency = urgencyFromDate(input.expiresOn)
    if (input.expiresOn && urgencyRank[incomingUrgency] > urgencyRank[existing.urgency]) {
      existing.expiresOn = input.expiresOn
      existing.urgency = incomingUrgency
      existing.urgencyKey = undefined
    }
  } else {
    inventory.value.push({
      id: `${input.foodKey}-${input.location}-${crypto.randomUUID()}`,
      ...input,
      quantity: storedQuantity,
      unit: baseUnit,
      nameKey: input.nameKey ?? registerCustomFoodNames(input.foodKey, input.names),
      urgency: urgencyFromDate(input.expiresOn),
    })
  }
  persist()
}

const urgencyMap: Record<StorageApiItem['urgency'], { urgency: Urgency; urgencyKey?: string }> = {
  PAST_DATE: { urgency: 'past', urgencyKey: 'urgency.past' },
  TODAY: { urgency: 'today', urgencyKey: 'urgency.today' },
  ONE_TO_TWO_DAYS: { urgency: 'soon', urgencyKey: 'urgency.oneToTwo' },
  THREE_TO_FIVE_DAYS: { urgency: 'later', urgencyKey: 'urgency.threeToFive' },
  LATER: { urgency: 'neutral' },
}

function mapApiItem(item: StorageApiItem): InventoryFood {
  const catalogItem = foodCatalog.find((food) => food.foodKey === item.foodKey)
  const names = { en: item.names.en, 'zh-CN': item.names['zh-CN'] ?? item.names.en }
  if (item.visualKey && item.visualKey !== item.foodKey) {
    registerVisualKey(item.foodKey, item.visualKey)
  }
  if ('customIcon' in item && item.customIcon) {
    registerCustomIcon(item.foodKey, item.customIcon)
  }
  return {
    id: `${item.foodKey}-${item.location}`,
    foodKey: item.foodKey,
    nameKey: catalogItem?.nameKey ?? registerCustomFoodNames(item.foodKey, names),
    names,
    quantity: Number(item.quantity),
    unit: normalizeLegacyInventoryUnit(item.unit),
    location: item.location.toLocaleLowerCase() as StorageLocation,
    ...urgencyMap[item.urgency],
  }
}

async function refreshInventoryFromServer(): Promise<boolean> {
  try {
    const response = await fetchStorage()
    const catalogOrder = new Map(foodCatalog.map((food, index) => [food.foodKey, index]))
    inventory.value = response.inventory
      .map(mapApiItem)
      .sort((left, right) => (catalogOrder.get(left.foodKey) ?? 999) - (catalogOrder.get(right.foodKey) ?? 999))
    persist()
    syncState.value = 'synced'
    return true
  } catch {
    syncState.value = 'local-only'
    return false
  }
}

let sharedHydration: Promise<boolean> | undefined

function hydrateFromServer(): Promise<boolean> {
  if (sharedHydration) return sharedHydration

  const hydration = refreshInventoryFromServer()
  sharedHydration = hydration
  void hydration.finally(() => {
    setTimeout(() => {
      if (sharedHydration === hydration) sharedHydration = undefined
    }, 0)
  })
  return hydration
}

async function checkIn(input: CheckInInput): Promise<boolean> {
  try {
    await persistCheckIn(input, crypto.randomUUID())
    return await refreshInventoryFromServer()
  } catch {
    checkInLocally(input)
    syncState.value = 'local-only'
    return false
  }
}

export interface UpdateLotInput {
  quantity?: number
  unit?: InventoryUnit
  location?: StorageLocation
  /** Required ISO local date when correcting when the lot was stored. */
  storedOn?: string
  /** ISO date, or null to clear the use-by date. */
  expiresOn?: string | null
}

/**
 * Server-backed lot mutations (UI-03). Unlike checkIn these have no local
 * fallback: failures throw so the calling view can surface an error message.
 * Every successful mutation rehydrates the aggregate inventory from the server.
 */
async function updateLot(lotId: string, input: UpdateLotInput): Promise<boolean> {
  const patch: PatchLotInput = {}
  if (input.quantity !== undefined) patch.quantity = String(input.quantity)
  if (input.unit !== undefined) patch.unit = input.unit
  if (input.location !== undefined) patch.location = input.location.toUpperCase() as ApiLocation
  if (input.storedOn !== undefined) patch.storedOn = input.storedOn
  if (input.expiresOn !== undefined) patch.expiresOn = input.expiresOn
  await patchLot(lotId, patch, crypto.randomUUID())
  return refreshInventoryFromServer()
}

async function reduceStock(input: { foodKey: string; location: StorageLocation; amount: number; unit: InventoryUnit }): Promise<boolean> {
  await reduceInventory(
    {
      foodKey: input.foodKey,
      location: input.location.toUpperCase() as ApiLocation,
      amount: String(input.amount),
      unit: input.unit,
    },
    crypto.randomUUID(),
  )
  return refreshInventoryFromServer()
}

async function discardLotById(lotId: string): Promise<boolean> {
  await discardLot(lotId, crypto.randomUUID())
  return refreshInventoryFromServer()
}

export function useInventoryStore() {
  return {
    inventory,
    useSoonFoods: computed(() => inventory.value.filter((food) => food.urgency !== 'neutral')),
    syncState,
    hydrateFromServer,
    checkIn,
    updateLot,
    reduceStock,
    discardLotById,
  }
}
