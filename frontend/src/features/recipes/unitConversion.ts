/**
 * Recipe unit conversion utilities.
 *
 * AI-generated recipes may use cooking units (tbsp, tsp, cup, oz, etc.) that
 * are not in the Fridge Pal canonical unit set: g, kg, ml, l, piece.
 * These functions convert common cooking units to the nearest system unit so
 * that every displayed quantity is expressed in a unit the user can select.
 *
 * Conversions are approximate but deterministic — they are display-only and
 * never write to Storage.  The backend LLM prompt is also updated to prefer
 * system units, so this acts as a safety net.
 */

import { inventoryUnits, type InventoryUnit } from '../storage/inventory'

interface ConversionEntry {
  toUnit: InventoryUnit
  factor: number
}

/**
 * Lookup table for non-system cooking units.
 * Keys are lowercased singular forms; aliases are listed explicitly.
 */
const COOKING_UNIT_CONVERSIONS: Record<string, ConversionEntry> = {
  // Volume → ml
  tbsp: { toUnit: 'g', factor: 15 },
  tablespoon: { toUnit: 'g', factor: 15 },
  tablespoons: { toUnit: 'g', factor: 15 },
  tsp: { toUnit: 'g', factor: 5 },
  teaspoon: { toUnit: 'g', factor: 5 },
  teaspoons: { toUnit: 'g', factor: 5 },
  cup: { toUnit: 'ml', factor: 240 },
  cups: { toUnit: 'ml', factor: 240 },
  'fl oz': { toUnit: 'ml', factor: 30 },
  'fluid ounce': { toUnit: 'ml', factor: 30 },
  'fluid ounces': { toUnit: 'ml', factor: 30 },
  pint: { toUnit: 'ml', factor: 473 },
  pints: { toUnit: 'ml', factor: 473 },
  quart: { toUnit: 'ml', factor: 946 },
  quarts: { toUnit: 'ml', factor: 946 },
  gallon: { toUnit: 'ml', factor: 3785 },
  gallons: { toUnit: 'ml', factor: 3785 },
  dash: { toUnit: 'ml', factor: 0.5 },
  pinch: { toUnit: 'ml', factor: 0.3 },

  // Weight → g
  oz: { toUnit: 'g', factor: 28 },
  ounce: { toUnit: 'g', factor: 28 },
  ounces: { toUnit: 'g', factor: 28 },
  lb: { toUnit: 'g', factor: 454 },
  lbs: { toUnit: 'g', factor: 454 },
  pound: { toUnit: 'g', factor: 454 },
  pounds: { toUnit: 'g', factor: 454 },

  // Count → piece
  head: { toUnit: 'piece', factor: 1 },
  heads: { toUnit: 'piece', factor: 1 },
  bulb: { toUnit: 'piece', factor: 1 },
  bulbs: { toUnit: 'piece', factor: 1 },
  clove: { toUnit: 'piece', factor: 1 },
  cloves: { toUnit: 'piece', factor: 1 },
  bunch: { toUnit: 'piece', factor: 1 },
  bunches: { toUnit: 'piece', factor: 1 },
  can: { toUnit: 'piece', factor: 1 },
  cans: { toUnit: 'piece', factor: 1 },
  package: { toUnit: 'piece', factor: 1 },
  packages: { toUnit: 'piece', factor: 1 },
  stick: { toUnit: 'piece', factor: 1 },
  sticks: { toUnit: 'piece', factor: 1 },
  slice: { toUnit: 'piece', factor: 1 },
  slices: { toUnit: 'piece', factor: 1 },
  handful: { toUnit: 'piece', factor: 1 },
  handfuls: { toUnit: 'piece', factor: 1 },
}

export interface ConvertedAmount {
  value: number | null
  unit: string
  converted: boolean
}

/**
 * Convert a recipe ingredient amount + unit to system units.
 *
 * - Returns `{ value: null, unit, converted: false }` when the amount is
 *   missing, non-numeric, or zero (zero amounts are treated as "as needed").
 * - Returns the original values when the unit is already a system unit.
 * - Converts known cooking units (tbsp, tsp, cup, oz, lb, …) to ml or g.
 * - Returns the original unit when no conversion is known.
 */
export function convertToSystemUnit(
  amount: string | null | undefined,
  unit: string | null | undefined,
): ConvertedAmount {
  if (amount === null || amount === undefined || amount.trim() === '') {
    return { value: null, unit: unit ?? '', converted: false }
  }

  const parsed = parseFloat(amount)
  if (isNaN(parsed) || parsed === 0) {
    return { value: null, unit: unit ?? '', converted: false }
  }

  const normalizedUnit = (unit ?? '').trim().toLowerCase()

  if (normalizedUnit && (inventoryUnits as readonly string[]).includes(normalizedUnit)) {
    return { value: parsed, unit: normalizedUnit, converted: false }
  }

  const entry = COOKING_UNIT_CONVERSIONS[normalizedUnit]
  if (entry) {
    return {
      value: Math.round(parsed * entry.factor * 100) / 100,
      unit: entry.toUnit,
      converted: true,
    }
  }

  return { value: parsed, unit: unit ?? '', converted: false }
}

export function formatConvertedAmount(converted: ConvertedAmount): string {
  if (converted.value === null) {
    return 'As needed'
  }
  const unitPart = converted.unit ? ` ${converted.unit}` : ''
  return `${converted.value}${unitPart}`
}

export function formatRecipeAmount(
  amount: string | null | undefined,
  unit: string | null | undefined,
): string {
  return formatConvertedAmount(convertToSystemUnit(amount, unit))
}

const SEASONING_KEYWORDS = [
  'salt', 'pepper', 'oil', 'soy sauce', 'vinegar', 'sugar', 'honey',
  'paprika', 'cumin', 'oregano', 'basil', 'thyme', 'bay leaf', 'cinnamon',
  'nutmeg', 'turmeric', 'coriander', 'parsley', 'rosemary', 'dill', 'sage',
  'mint', 'curry powder', 'curry paste', 'fish sauce', 'oyster sauce',
  'hoisin sauce', 'sriracha', 'cooking wine', 'rice wine', 'cornstarch',
  'baking soda', 'baking powder', 'mustard', 'ketchup', 'mayonnaise',
  'worcestershire', 'sesame oil', 'sesame seed', 'chili powder', 'chili flake',
  'cayenne', 'garlic powder', 'onion powder', 'ginger powder',
  'starch', 'yeast', 'vanilla', 'cocoa powder',
  '盐', '胡椒', '油', '酱油', '生抽', '老抽', '醋', '糖', '冰糖',
  '蜂蜜', '辣椒粉', '咖喱粉', '料酒', '黄酒', '淀粉', '生粉',
  '小苏打', '泡打粉', '酵母', '蚝油', '鱼露', '甜面酱', '豆瓣酱',
  '芝麻油', '香油', '花椒', '八角', '桂皮', '香叶', '孜然',
  '五香粉', '十三香', '豆豉', '腐乳',
]

export function isSeasoning(ingredient: {
  needsReview?: boolean
  originalText?: string
  amount?: string | null
  unit?: string | null
  baseQuantity?: number | null
  nameKey?: string
}): boolean {
  const hasAmount = (() => {
    if (ingredient.baseQuantity !== undefined && ingredient.baseQuantity !== null && ingredient.baseQuantity > 0) return true
    const converted = convertToSystemUnit(ingredient.amount, ingredient.unit)
    return converted.value !== null
  })()
  if (hasAmount) return false
  if (ingredient.needsReview) return true
  const text = (ingredient.originalText ?? ingredient.nameKey ?? '').toLowerCase()
  return SEASONING_KEYWORDS.some((kw) => text.includes(kw))
}

export function formatSeasoningAmount(
  amount: string | null | undefined,
  unit: string | null | undefined,
): string {
  const converted = convertToSystemUnit(amount, unit)
  if (converted.value === null) return ''
  const unitPart = converted.unit ? ` ${converted.unit}` : ''
  return `${converted.value}${unitPart}`
}
