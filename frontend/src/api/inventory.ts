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

export type ApiLocation = 'FRIDGE' | 'FREEZER' | 'PANTRY'

export interface InventoryLot {
  lotId: string
  quantity: string
  unit: string
  location: ApiLocation
  storedOn: string
  expiresOn: string | null
  expirySource: string
  status: 'ACTIVE' | 'DEPLETED' | 'CONSUMED' | 'DISCARDED'
}

interface LotsResponse {
  lots: InventoryLot[]
}

export interface PatchLotInput {
  quantity?: string
  unit?: string
  location?: ApiLocation
  storedOn?: string
  expiresOn?: string | null
}

interface LotMutationResponse {
  lotId: string
  replayed: boolean
}

export interface ReduceAllocation {
  lotId: string
  deducted: string
}

export interface ReduceResponse {
  newQuantity: string
  replayed: boolean
  allocations: ReduceAllocation[]
}

/** Thrown when the server rejects a reduction because the amount exceeds availability (409). */
export class InsufficientQuantityError extends Error {}

/** Thrown when a cooking commit's lot snapshots no longer match live quantities (409 stale preview). */
export class StalePreviewError extends Error {}

export interface CookingPreviewItem {
  foodKey: string
  amount: string
  unit: string
}

export interface CookingAllocation {
  lotId: string
  quantity: string
  /** Snapshot of the lot's live quantity at preview time; the commit revalidates it. */
  lotQuantity: string
}

export interface CookingPreviewLine {
  foodKey: string
  requested: string
  allocated: string
  shortfall: string
  allocations: CookingAllocation[]
}

export interface CookingPreviewResponse {
  lines: CookingPreviewLine[]
  feasible: boolean
}

export interface CookingCommitLine {
  foodKey: string
  allocations: CookingAllocation[]
}

export interface CookingCommitResponse {
  sessionId: string
  replayed: boolean
}

export async function cookingPreview(items: CookingPreviewItem[]): Promise<CookingPreviewResponse> {
  const response = await fetch('/api/cooking/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ items }),
  })
  if (!response.ok) throw new Error(`Cooking preview failed with status ${response.status}`)
  return response.json() as Promise<CookingPreviewResponse>
}

export async function cookingCommit(
  input: { idempotencyKey: string; sessionName?: string; lines: CookingCommitLine[] },
): Promise<CookingCommitResponse> {
  const response = await fetch('/api/cooking/commit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(input),
  })
  if (!response.ok) {
    const detail = await readErrorDetail(response)
    if (response.status === 409 && detail.includes('stale')) {
      throw new StalePreviewError(detail)
    }
    throw new Error(`Cooking commit failed with status ${response.status}`)
  }
  return response.json() as Promise<CookingCommitResponse>
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string }
    return body.detail ?? ''
  } catch {
    return ''
  }
}

export async function persistCheckIn(input: CheckInInput, idempotencyKey: string): Promise<CheckInResponse> {
  const response = await fetch('/api/inventory/check-in', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
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
  const response = await fetch('/api/storage', { credentials: 'include' })
  if (!response.ok) throw new Error(`Storage fetch failed with status ${response.status}`)
  return response.json() as Promise<StorageResponse>
}

/** Lots for one food/location pair, in server (FEFO) order, excluding discarded lots. */
export async function fetchLots(foodKey: string, location: ApiLocation): Promise<InventoryLot[]> {
  const params = new URLSearchParams({ foodKey, location })
  const response = await fetch(`/api/inventory/lots?${params}`, { credentials: 'include' })
  if (!response.ok) throw new Error(`Lots fetch failed with status ${response.status}`)
  const body = (await response.json()) as LotsResponse
  return body.lots
}

export async function patchLot(lotId: string, input: PatchLotInput, idempotencyKey: string): Promise<LotMutationResponse> {
  const response = await fetch(`/api/lots/${encodeURIComponent(lotId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ idempotencyKey, ...input }),
  })
  if (!response.ok) throw new Error(`Lot update failed with status ${response.status}`)
  return response.json() as Promise<LotMutationResponse>
}

export async function reduceInventory(
  input: { foodKey: string; location: ApiLocation; amount: string; unit: string },
  idempotencyKey: string,
): Promise<ReduceResponse> {
  const response = await fetch('/api/inventory/reduce', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ idempotencyKey, ...input }),
  })
  if (!response.ok) {
    const detail = await readErrorDetail(response)
    if (response.status === 409 && detail.includes('insufficient')) {
      throw new InsufficientQuantityError(detail)
    }
    throw new Error(`Inventory reduce failed with status ${response.status}`)
  }
  return response.json() as Promise<ReduceResponse>
}

export async function discardLot(lotId: string, idempotencyKey: string): Promise<LotMutationResponse> {
  const response = await fetch(`/api/lots/${encodeURIComponent(lotId)}/discard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ idempotencyKey }),
  })
  if (!response.ok) throw new Error(`Lot discard failed with status ${response.status}`)
  return response.json() as Promise<LotMutationResponse>
}
