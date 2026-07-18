import type { CheckInInput } from '../features/storage/inventoryStore'

export interface StorageApiItem {
  foodKey: string
  names: { en: string; 'zh-CN'?: string }
  visualKey: string
  quantity: string
  unit: string
  location: 'FRIDGE' | 'FREEZER' | 'PANTRY'
  urgency: 'PAST_DATE' | 'TODAY' | 'ONE_TO_TWO_DAYS' | 'THREE_TO_FIVE_DAYS' | 'LATER'
}

interface StorageResponse {
  useSoon: StorageApiItem[]
  inventory: StorageApiItem[]
}

interface CheckInResponse {
  lotId: string
  activityEventId: string
  replayed: boolean
}

export async function persistCheckIn(input: CheckInInput, idempotencyKey: string): Promise<CheckInResponse> {
  const response = await fetch('/api/inventory/check-in', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      idempotencyKey,
      foodKey: input.foodKey,
      names: input.names,
      quantity: input.quantity.toString(),
      unit: input.unit,
      location: input.location.toUpperCase(),
      storedOn: input.storedOn,
      expiresOn: input.expiresOn,
      expirySource: input.expiresOn ? 'LIBRARY_DEFAULT' : 'NONE',
    }),
  })
  if (!response.ok) {
    throw new Error(`Inventory check-in failed with status ${response.status}`)
  }
  return response.json() as Promise<CheckInResponse>
}

export async function fetchStorage(): Promise<StorageResponse> {
  const response = await fetch('/api/storage')
  if (!response.ok) throw new Error(`Storage fetch failed with status ${response.status}`)
  return response.json() as Promise<StorageResponse>
}
