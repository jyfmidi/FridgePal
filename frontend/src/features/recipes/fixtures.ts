import type { InventoryFood } from '../storage/inventory'

export interface RecipeSourceFixture {
  id: string
  title: string
  publisher: string
  domain: string
  url: string
  serves?: number
  usedFoodKeys: string[]
}

export interface PlanIngredient {
  id: string
  nameKey: string
  amount: string
}

export const recipeSources: RecipeSourceFixture[] = [
  {
    id: 'stuffed-chicken-breast',
    title: 'Stuffed chicken breast',
    publisher: 'Good Food',
    domain: 'bbcgoodfood.com',
    url: 'https://www.bbcgoodfood.com/recipes/cheese-spinach-mushroom-stuffed-chicken',
    serves: 4,
    usedFoodKeys: ['chicken-breast', 'spinach', 'mushrooms', 'garlic'],
  },
  {
    id: 'creamy-spinach-mushroom-penne',
    title: 'Creamy spinach & mushroom penne',
    publisher: 'Good Food',
    domain: 'bbcgoodfood.com',
    url: 'https://www.bbcgoodfood.com/recipes/creamy-spinach-mushroom-penne',
    serves: 2,
    usedFoodKeys: ['spinach', 'mushrooms', 'pasta', 'garlic'],
  },
  {
    id: 'chicken-and-mushrooms',
    title: 'Chicken and mushrooms',
    publisher: 'Good Food',
    domain: 'bbcgoodfood.com',
    url: 'https://www.bbcgoodfood.com/recipes/chicken-mushrooms',
    usedFoodKeys: ['chicken-breast', 'mushrooms', 'frozen-peas'],
  },
]

const amountByFoodKey: Record<string, string> = {
  'chicken-breast': '300 g',
  spinach: '120 g',
  mushrooms: '180 g',
  broccoli: '200 g',
  tofu: '200 g',
  yogurt: '120 g',
  lemon: '1',
  eggs: '2',
  milk: '120 ml',
  carrots: '160 g',
  tomatoes: '200 g',
  onion: '1',
  garlic: '10 g',
  rice: '160 g',
  pasta: '180 g',
  'frozen-peas': '140 g',
}

export function buildPlanIngredients(foods: InventoryFood[]): PlanIngredient[] {
  return foods.map((food) => ({
    id: food.id,
    nameKey: food.nameKey,
    amount: amountByFoodKey[food.foodKey] ?? 'As needed',
  }))
}
