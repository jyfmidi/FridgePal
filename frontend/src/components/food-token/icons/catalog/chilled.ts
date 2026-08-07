import { palette as c } from './palette'
import { circle, path, rect } from './primitives'
import type { FoodIconDefinitionMap } from './types'

export const chilledIconDefinitions = {
  tofu: [
    path('M7 19 21 7l20 8-14 13L7 19Z', c.creamLight),
    path('M7 19v17l20 7V28L7 19Z', c.cream),
    path('M27 28 41 15v17L27 43V28Z', c.creamDark),
    circle(19, 17, 1.4, c.tanLight), circle(27, 15, 1.2, c.tanLight), circle(32, 19, 1.1, c.tanLight),
  ],
  'dried-tofu': [
    path('M6 18 20 7l22 8-14 13L6 18Z', c.tanLight),
    path('M6 18v18l22 7V28L6 18Z', c.tan),
    path('M28 28 42 15v18L28 43V28Z', c.brown),
    path('M12 23l11 4m-11 3 11 4m10-5 5-5m-5 12 5-5', 'none', { stroke: c.brownDark, 'stroke-width': 1.3, 'stroke-linecap': 'round' }),
  ],
  milk: [
    path('M14 9h17l5 8v26H10V17l4-8Z', c.white),
    path('M27 9h4l5 8v26H27V9Z', c.milkBlue),
    path('M14 9V4h17v5H14Z', c.milkBlueDark),
    path('M10 18h26v10H10V18Z', c.milkBlueDark),
    path('M19 23c0-3 2-5 5-7 3 2 5 4 5 7 0 3-2 5-5 5s-5-2-5-5Z', c.white),
  ],
  yogurt: [
    path('M10 14h28l-3 28H13l-3-28Z', c.white),
    path('M25 14h13l-3 28H25V14Z', c.creamDark),
    rect(8, 9, 32, 8, 4, c.milkBlueDark),
    circle(24, 29, 7, c.pink),
    path('M20 31c3-5 7-6 11-3-3 5-7 7-11 3Z', c.pinkLight),
  ],
} satisfies FoodIconDefinitionMap
