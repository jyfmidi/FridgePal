import { apiFetch } from './client'

/** One active Food Library entry as served to every user (Add Food typeahead). */
export interface LibraryFood {
  foodKey: string
  names: { en: string; 'zh-CN'?: string }
  aliases: Record<string, string[]>
  category: string
  visualKey: string
  baseUnit: 'g' | 'kg' | 'ml' | 'l' | 'piece'
  roundingIncrement: string | null
  packagePresets: { label: { en: string; 'zh-CN'?: string }; amount: string; unit: string }[]
  recommendedStorage: 'FRIDGE' | 'FREEZER' | 'PANTRY'
  origin: 'SEEDED' | 'USER_CREATED'
  active: boolean
  /** Admin-uploaded custom icon as a data URI (SVG or PNG), or null. */
  customIcon: string | null
  shelfLife: { storageLocation: 'FRIDGE' | 'FREEZER' | 'PANTRY'; durationDays: number; sourceNote: string | null }[]
}

export async function fetchFoodLibrary(): Promise<LibraryFood[]> {
  const res = await apiFetch('/api/library')
  if (!res.ok) throw new Error('Failed to load the Food Library')
  return res.json()
}
