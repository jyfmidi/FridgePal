import { i18n } from '../i18n'
import { apiFetch } from './client'
import type { LibraryFood } from './library'

export interface FoodDefinitionPayload {
  foodKey?: string
  names: { en: string; 'zh-CN'?: string }
  aliases: Record<string, string[]>
  category: string
  visualKey: string
  baseUnit: 'g' | 'kg' | 'ml' | 'l' | 'piece'
  roundingIncrement?: string
  packagePresets: { label: { en: string; 'zh-CN'?: string }; amount: string; unit: string }[]
  recommendedStorage: 'FRIDGE' | 'FREEZER' | 'PANTRY'
  active: boolean
  shelfLife: { storageLocation: 'FRIDGE' | 'FREEZER' | 'PANTRY'; durationDays: number }[]
}

export interface AdminSettings {
  useSoonWindowDays: number
}

/** Stable backend error codes mapped to i18n keys. */
const ADMIN_ERROR_I18N: Record<string, string> = {
  ADMIN_REQUIRED: 'admin.errors.required',
  ADMIN_FOOD_EXISTS: 'admin.errors.foodExists',
  ADMIN_FOOD_NOT_FOUND: 'admin.errors.foodNotFound',
  ADMIN_KEY_INVALID: 'admin.errors.keyInvalid',
  ADMIN_NAME_REQUIRED: 'admin.errors.nameRequired',
  ADMIN_UNIT_INVALID: 'admin.errors.unitInvalid',
  ADMIN_UNIT_CHANGE_CONFLICT: 'admin.errors.unitChangeConflict',
  ADMIN_LOCATION_INVALID: 'admin.errors.locationInvalid',
  ADMIN_RULE_INVALID: 'admin.errors.ruleInvalid',
  ADMIN_PRESET_INVALID: 'admin.errors.presetInvalid',
  ADMIN_SETTING_INVALID: 'admin.errors.settingInvalid',
  ADMIN_ICON_INVALID: 'admin.errors.iconInvalid',
  ADMIN_ICON_TOO_LARGE: 'admin.errors.iconTooLarge',
}

async function adminErrorMessage(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => null)
  const detail: unknown = body?.detail
  if (typeof detail === 'string' && ADMIN_ERROR_I18N[detail]) {
    return i18n.global.t(ADMIN_ERROR_I18N[detail])
  }
  return fallback
}

async function adminFetch(path: string, init?: RequestInit, fallbackKey = 'admin.errors.generic') {
  const res = await apiFetch(path, init)
  if (!res.ok) {
    throw new Error(await adminErrorMessage(res, i18n.global.t(fallbackKey)))
  }
  return res
}

export async function listFoodDefinitions(): Promise<LibraryFood[]> {
  const res = await adminFetch('/api/admin/foods')
  return res.json()
}

export async function createFoodDefinition(payload: FoodDefinitionPayload): Promise<LibraryFood> {
  const res = await adminFetch('/api/admin/foods', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res.json()
}

export async function updateFoodDefinition(
  foodKey: string,
  payload: FoodDefinitionPayload,
): Promise<LibraryFood> {
  const res = await adminFetch(`/api/admin/foods/${encodeURIComponent(foodKey)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return res.json()
}

export async function deleteFoodDefinition(foodKey: string): Promise<void> {
  await adminFetch(`/api/admin/foods/${encodeURIComponent(foodKey)}`, { method: 'DELETE' })
}

/** Uploads a custom icon (SVG or PNG); returns the updated food definition. */
export async function uploadFoodIcon(foodKey: string, file: File): Promise<LibraryFood> {
  const form = new FormData()
  form.append('file', file)
  const res = await adminFetch(`/api/admin/foods/${encodeURIComponent(foodKey)}/icon`, {
    method: 'POST',
    body: form,
  }, 'admin.errors.iconUploadFailed')
  return res.json()
}

/** Removes the custom icon; returns the updated food definition. */
export async function removeFoodIcon(foodKey: string): Promise<LibraryFood> {
  const res = await adminFetch(`/api/admin/foods/${encodeURIComponent(foodKey)}/icon`, {
    method: 'DELETE',
  })
  return res.json()
}

export async function fetchAdminSettings(): Promise<AdminSettings> {
  const res = await adminFetch('/api/admin/settings')
  return res.json()
}

export async function saveAdminSettings(settings: AdminSettings): Promise<AdminSettings> {
  const res = await adminFetch('/api/admin/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  return res.json()
}
