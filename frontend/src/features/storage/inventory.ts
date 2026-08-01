export type StorageLocation = 'fridge' | 'freezer' | 'pantry'
export type Urgency = 'past' | 'today' | 'soon' | 'later' | 'neutral'
export const inventoryUnits = ['g', 'kg', 'ml', 'l', 'piece'] as const
export type InventoryUnit = (typeof inventoryUnits)[number]

const legacyCountUnits = new Set(['head', 'bulb', 'clove', 'bunch'])

export function isInventoryUnit(value: string): value is InventoryUnit {
  return inventoryUnits.includes(value as InventoryUnit)
}

export function normalizeLegacyInventoryUnit(value: string): string {
  const normalized = value.trim().toLowerCase()
  return legacyCountUnits.has(normalized) ? 'piece' : normalized
}

export function compatibleInventoryUnits(unit: InventoryUnit): InventoryUnit[] {
  if (unit === 'g' || unit === 'kg') return ['g', 'kg']
  if (unit === 'ml' || unit === 'l') return ['ml', 'l']
  return ['piece']
}

export function convertInventoryQuantity(value: number, from: InventoryUnit, to: InventoryUnit): number {
  if (from === to) return value
  if (from === 'g' && to === 'kg') return value / 1000
  if (from === 'kg' && to === 'g') return value * 1000
  if (from === 'ml' && to === 'l') return value / 1000
  if (from === 'l' && to === 'ml') return value * 1000
  throw new Error(`Cannot convert ${from} to ${to} without food-specific metadata`)
}

export function roundInventoryQuantity(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000
}

export interface InventoryFood {
  id: string
  foodKey: string
  nameKey: string
  /** Raw localized names, kept so custom foods survive a local-only reload. */
  names?: { en: string; 'zh-CN': string }
  quantity: number
  /** Canonical Storage unit. Legacy local records are normalized during hydration. */
  unit: string
  location: StorageLocation
  urgency: Urgency
  urgencyKey?: string
  storedOn?: string
  expiresOn?: string
}

export const demoInventory: InventoryFood[] = [
  { id: 'spinach', foodKey: 'spinach', nameKey: 'foods.spinach', quantity: 250, unit: 'g', location: 'fridge', urgency: 'today', urgencyKey: 'urgency.today' },
  { id: 'yogurt', foodKey: 'yogurt', nameKey: 'foods.yogurt', quantity: 300, unit: 'g', location: 'fridge', urgency: 'today', urgencyKey: 'urgency.today' },
  { id: 'chicken', foodKey: 'chicken-breast', nameKey: 'foods.chickenBreast', quantity: 600, unit: 'g', location: 'fridge', urgency: 'soon', urgencyKey: 'urgency.tomorrow' },
  { id: 'mushrooms', foodKey: 'mushrooms', nameKey: 'foods.mushrooms', quantity: 300, unit: 'g', location: 'fridge', urgency: 'soon', urgencyKey: 'urgency.twoDays' },
  { id: 'broccoli', foodKey: 'broccoli', nameKey: 'foods.broccoli', quantity: 300, unit: 'g', location: 'fridge', urgency: 'soon', urgencyKey: 'urgency.twoDays' },
  { id: 'tofu', foodKey: 'tofu', nameKey: 'foods.tofu', quantity: 400, unit: 'g', location: 'fridge', urgency: 'later', urgencyKey: 'urgency.threeDays' },
  { id: 'lemon', foodKey: 'lemon', nameKey: 'foods.lemon', quantity: 3, unit: 'piece', location: 'fridge', urgency: 'later', urgencyKey: 'urgency.threeDays' },
  { id: 'eggs', foodKey: 'eggs', nameKey: 'foods.eggs', quantity: 8, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'milk', foodKey: 'milk', nameKey: 'foods.milk', quantity: 900, unit: 'ml', location: 'fridge', urgency: 'neutral' },
  { id: 'carrots', foodKey: 'carrots', nameKey: 'foods.carrots', quantity: 5, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'tomatoes', foodKey: 'tomatoes', nameKey: 'foods.tomatoes', quantity: 4, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'onion', foodKey: 'onion', nameKey: 'foods.onion', quantity: 6, unit: 'piece', location: 'pantry', urgency: 'neutral' },
  { id: 'garlic', foodKey: 'garlic', nameKey: 'foods.garlic', quantity: 80, unit: 'g', location: 'pantry', urgency: 'neutral' },
  { id: 'rice', foodKey: 'rice', nameKey: 'foods.rice', quantity: 1.2, unit: 'kg', location: 'pantry', urgency: 'neutral' },
  { id: 'pasta', foodKey: 'pasta', nameKey: 'foods.pasta', quantity: 500, unit: 'g', location: 'pantry', urgency: 'neutral' },
  { id: 'peas', foodKey: 'frozen-peas', nameKey: 'foods.frozenPeas', quantity: 450, unit: 'g', location: 'freezer', urgency: 'neutral' },
]

export interface FoodCatalogItem {
  foodKey: string
  /** Catalog i18n key; absent for server-only foods whose names come from `names`. */
  nameKey?: string
  names: { en: string; 'zh-CN': string }
  defaultLocation: StorageLocation
  defaultQuantity: number
  defaultUnit: InventoryUnit
  /** Curated Food Token key; defaults to `foodKey` when absent. */
  visualKey?: string
  /** Search keywords per locale (admin-managed); matched by Add Food typeahead. */
  aliases?: Record<string, string[]>
  /** Quick quantity chips shown in Add Food (admin-managed package presets). */
  packagePresets?: { label: { en: string; 'zh-CN'?: string }; amount: number; unit: InventoryUnit }[]
  shelfLifeDays?: number
}

const catalogNames: Record<string, { en: string; 'zh-CN': string }> = {
  spinach: { en: 'Spinach', 'zh-CN': '菠菜' },
  yogurt: { en: 'Yogurt', 'zh-CN': '酸奶' },
  'chicken-breast': { en: 'Chicken breast', 'zh-CN': '鸡胸肉' },
  mushrooms: { en: 'Mushrooms', 'zh-CN': '蘑菇' },
  broccoli: { en: 'Broccoli', 'zh-CN': '西兰花' },
  tofu: { en: 'Tofu', 'zh-CN': '豆腐' },
  lemon: { en: 'Lemon', 'zh-CN': '柠檬' },
  eggs: { en: 'Eggs', 'zh-CN': '鸡蛋' },
  milk: { en: 'Milk', 'zh-CN': '牛奶' },
  carrots: { en: 'Carrots', 'zh-CN': '胡萝卜' },
  tomatoes: { en: 'Tomatoes', 'zh-CN': '番茄' },
  onion: { en: 'Onion', 'zh-CN': '洋葱' },
  garlic: { en: 'Garlic', 'zh-CN': '大蒜' },
  rice: { en: 'Rice', 'zh-CN': '大米' },
  pasta: { en: 'Pasta', 'zh-CN': '意面' },
  'frozen-peas': { en: 'Frozen peas', 'zh-CN': '冷冻豌豆' },
}

export const foodCatalog: FoodCatalogItem[] = demoInventory.map((food) => ({
  foodKey: food.foodKey,
  nameKey: food.nameKey,
  names: catalogNames[food.foodKey],
  defaultLocation: food.location,
  defaultQuantity: food.quantity,
  defaultUnit: food.unit as InventoryUnit,
  shelfLifeDays: food.location === 'fridge' ? 5 : undefined,
}))
