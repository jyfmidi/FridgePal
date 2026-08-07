import { palette as c } from './palette'
import { ellipse, path } from './primitives'
import type { FoodIconDefinitionMap } from './types'

/** Compatibility-only staples retained for existing FoodDefinition rows. */
export const legacyIconDefinitions = {
  rice: [
    path('M7 24h34l-4 18H11L7 24Z', c.milkBlueDark),
    path('M11 24h26l-3 14H14l-3-14Z', c.milkBlue),
    ellipse(24, 23, 16, 9, c.creamLight),
    ellipse(17, 21, 4, 2, c.cream, { transform: 'rotate(18 17 21)' }), ellipse(25, 19, 4, 2, c.white, { transform: 'rotate(-12 25 19)' }), ellipse(31, 23, 4, 2, c.cream, { transform: 'rotate(22 31 23)' }),
  ],
  pasta: [
    path('M14 5h19l5 38H9l5-38Z', c.yellowLight, { transform: 'rotate(-12 24 24)' }),
    path('M14 6 10 42M18 6l-4 36M22 6l-3 36M26 6v36m4-36 2 36m1-36 4 36', 'none', { stroke: c.yellowDark, 'stroke-width': 1.6, 'stroke-linecap': 'butt', transform: 'rotate(-12 24 24)' }),
    path('M11 23h25l1 7H10l1-7Z', c.orangeDark, { transform: 'rotate(-12 24 24)' }),
    path('M13 24h22l-1 3H12l1-3Z', c.yellow, { transform: 'rotate(-12 24 24)' }),
  ],
} satisfies FoodIconDefinitionMap
