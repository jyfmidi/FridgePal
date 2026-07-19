export type StorageLocation = 'fridge' | 'freezer' | 'pantry'
export type Urgency = 'past' | 'today' | 'soon' | 'later' | 'neutral'
export type InventoryUnit = 'g' | 'kg' | 'ml' | 'piece' | 'head' | 'bulb'

export interface InventoryFood {
  id: string
  foodKey: string
  nameKey: string
  /** Raw localized names, kept so custom foods survive a local-only reload. */
  names?: { en: string; 'zh-CN': string }
  quantity: number
  /** Free-form unit string; catalog foods use the InventoryUnit vocabulary. */
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
  { id: 'broccoli', foodKey: 'broccoli', nameKey: 'foods.broccoli', quantity: 1, unit: 'head', location: 'fridge', urgency: 'soon', urgencyKey: 'urgency.twoDays' },
  { id: 'tofu', foodKey: 'tofu', nameKey: 'foods.tofu', quantity: 400, unit: 'g', location: 'fridge', urgency: 'later', urgencyKey: 'urgency.threeDays' },
  { id: 'lemon', foodKey: 'lemon', nameKey: 'foods.lemon', quantity: 3, unit: 'piece', location: 'fridge', urgency: 'later', urgencyKey: 'urgency.threeDays' },
  { id: 'eggs', foodKey: 'eggs', nameKey: 'foods.eggs', quantity: 8, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'milk', foodKey: 'milk', nameKey: 'foods.milk', quantity: 900, unit: 'ml', location: 'fridge', urgency: 'neutral' },
  { id: 'carrots', foodKey: 'carrots', nameKey: 'foods.carrots', quantity: 5, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'tomatoes', foodKey: 'tomatoes', nameKey: 'foods.tomatoes', quantity: 4, unit: 'piece', location: 'fridge', urgency: 'neutral' },
  { id: 'onion', foodKey: 'onion', nameKey: 'foods.onion', quantity: 6, unit: 'piece', location: 'pantry', urgency: 'neutral' },
  { id: 'garlic', foodKey: 'garlic', nameKey: 'foods.garlic', quantity: 2, unit: 'bulb', location: 'pantry', urgency: 'neutral' },
  { id: 'rice', foodKey: 'rice', nameKey: 'foods.rice', quantity: 1.2, unit: 'kg', location: 'pantry', urgency: 'neutral' },
  { id: 'pasta', foodKey: 'pasta', nameKey: 'foods.pasta', quantity: 500, unit: 'g', location: 'pantry', urgency: 'neutral' },
  { id: 'peas', foodKey: 'frozen-peas', nameKey: 'foods.frozenPeas', quantity: 450, unit: 'g', location: 'freezer', urgency: 'neutral' },
]

export interface FoodCatalogItem {
  foodKey: string
  nameKey: string
  names: { en: string; 'zh-CN': string }
  defaultLocation: StorageLocation
  defaultQuantity: number
  defaultUnit: InventoryUnit
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
