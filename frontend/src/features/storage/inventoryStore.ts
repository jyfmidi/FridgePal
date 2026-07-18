import { computed, ref } from 'vue'
import { fetchStorage, persistCheckIn, type StorageApiItem } from '../../api/inventory'
import { demoInventory, foodCatalog, type InventoryFood, type InventoryUnit, type StorageLocation, type Urgency } from './inventory'

const STORAGE_KEY = 'fridgital.inventory.v1'

function loadInventory(): InventoryFood[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return JSON.parse(saved) as InventoryFood[]
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
  nameKey: string
  names: { en: string; 'zh-CN': string }
  quantity: number
  unit: InventoryUnit
  location: StorageLocation
  storedOn: string
  expiresOn?: string
}

function checkInLocally(input: CheckInInput) {
  const existing = inventory.value.find(
    (food) => food.foodKey === input.foodKey && food.location === input.location && food.unit === input.unit,
  )

  if (existing) {
    existing.quantity += input.quantity
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

function mapApiItem(item: StorageApiItem): InventoryFood | null {
  const catalogItem = foodCatalog.find((food) => food.foodKey === item.foodKey)
  if (!catalogItem) return null
  return {
    id: `${item.foodKey}-${item.location}`,
    foodKey: item.visualKey,
    nameKey: catalogItem.nameKey,
    quantity: Number(item.quantity),
    unit: item.unit as InventoryUnit,
    location: item.location.toLocaleLowerCase() as StorageLocation,
    ...urgencyMap[item.urgency],
  }
}

async function hydrateFromServer(): Promise<boolean> {
  try {
    const response = await fetchStorage()
    const catalogOrder = new Map(foodCatalog.map((food, index) => [food.foodKey, index]))
    inventory.value = response.inventory
      .map(mapApiItem)
      .filter((food): food is InventoryFood => food !== null)
      .sort((left, right) => (catalogOrder.get(left.foodKey) ?? 999) - (catalogOrder.get(right.foodKey) ?? 999))
    persist()
    syncState.value = 'synced'
    return true
  } catch {
    syncState.value = 'local-only'
    return false
  }
}

async function checkIn(input: CheckInInput): Promise<boolean> {
  try {
    await persistCheckIn(input, crypto.randomUUID())
    return await hydrateFromServer()
  } catch {
    checkInLocally(input)
    syncState.value = 'local-only'
    return false
  }
}

export function useInventoryStore() {
  return {
    inventory,
    useSoonFoods: computed(() => inventory.value.filter((food) => food.urgency !== 'neutral')),
    syncState,
    hydrateFromServer,
    checkIn,
  }
}
