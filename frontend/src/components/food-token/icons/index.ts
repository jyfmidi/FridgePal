import type { Component } from 'vue'
import { chilledIconDefinitions } from './catalog/chilled'
import { fruitIconDefinitions } from './catalog/fruits'
import { legacyIconDefinitions } from './catalog/legacy'
import { proteinIconDefinitions } from './catalog/proteins'
import type { FoodIconDefinitionMap } from './catalog/types'
import { vegetableIconDefinitions } from './catalog/vegetables'
import { createFoodIcon } from './createFoodIcon'

/**
 * Food Token icon registry (UI-CMP-01).
 *
 * One coherent Bold Pantry family: 48x48 viewBox, semi-flat full color,
 * bold silhouette, two or three dominant fills, and shared top-left light.
 * The 70 approved household foods are accompanied by compatibility-only
 * rice and pasta keys so existing FoodDefinition rows keep rendering.
 */
const definitions = {
  ...vegetableIconDefinitions,
  ...fruitIconDefinitions,
  ...proteinIconDefinitions,
  ...chilledIconDefinitions,
  ...legacyIconDefinitions,
} satisfies FoodIconDefinitionMap

const EXPECTED_ICON_COUNT = 72
const entries = Object.entries(definitions)

if (import.meta.env.DEV && entries.length !== EXPECTED_ICON_COUNT) {
  throw new Error(`Food Token registry expected ${EXPECTED_ICON_COUNT} keys, received ${entries.length}`)
}

function componentName(key: string): string {
  return `Icon${key.split('-').map((part) => `${part[0]?.toUpperCase() ?? ''}${part.slice(1)}`).join('')}`
}

export const foodIcons: Record<string, Component> = Object.fromEntries(
  entries.map(([key, definition]) => [key, createFoodIcon(componentName(key), definition)]),
)
