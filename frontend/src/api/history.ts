export interface HistoryEvent {
  id: string
  eventType: 'CHECK_IN' | 'EDIT' | 'MOVE' | 'MANUAL_CONSUMPTION' | 'COOKING' | 'DISCARD' | 'REVERSAL'
  foodKey: string
  quantityDelta: string
  displaySnapshot: Record<string, unknown>
  createdAt: string
  reversible: boolean
}

export interface UndoResponse {
  eventId: string
  reversedTransactions: number
  replayed: boolean
}

export async function fetchHistory(limit: number = 50): Promise<HistoryEvent[]> {
  const response = await fetch(`/api/history?limit=${limit}`)
  if (!response.ok) throw new Error(`History fetch failed with status ${response.status}`)
  const body = await response.json() as { events: HistoryEvent[] }
  return body.events
}

export async function undoEvent(eventId: string, idempotencyKey: string): Promise<UndoResponse> {
  const response = await fetch(`/api/history/${encodeURIComponent(eventId)}/undo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idempotencyKey }),
  })
  if (!response.ok) {
    const detail = await readErrorDetail(response)
    throw new Error(detail || `Undo failed with status ${response.status}`)
  }
  return response.json() as Promise<UndoResponse>
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string }
    return body.detail ?? ''
  } catch {
    return ''
  }
}
