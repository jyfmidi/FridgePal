import { palette as c } from './palette'
import { circle, ellipse, line, path } from './primitives'
import type { FoodIconDefinitionMap } from './types'

export const proteinIconDefinitions = {
  eggs: [
    path('M8 31c0-10 4-22 11-22s11 12 11 22c0 8-5 13-11 13S8 39 8 31Z', c.cream),
    path('M20 29c0-9 4-20 10-20s10 11 10 20c0 8-4 13-10 13S20 37 20 29Z', c.creamLight),
    path('M12 27c1-7 3-13 7-15-3 7-3 17 0 27-4 0-7-5-7-12Z', c.tanLight),
  ],
  'chicken-breast': [
    path('M8 30C7 20 15 11 25 8c9-3 16 1 16 10 0 11-10 23-21 25C13 45 8 38 8 30Z', c.pink),
    path('M12 27c2-7 8-13 16-16-6 6-9 15-7 27-5 2-9-3-9-11Z', c.pinkLight),
    path('M21 40c8-4 14-11 18-20', 'none', { stroke: c.pinkDark, 'stroke-width': 1.7, 'stroke-linecap': 'round' }),
  ],
  'chicken-thigh': [
    path('M9 33c-4-6-1-13 6-15 2-10 13-15 21-9 8 6 5 18-3 24-7 6-18 7-24 0Z', c.pink),
    path('M13 31c-3-5 0-10 6-11 2-7 8-11 14-9-6 3-9 10-7 20-5 3-10 3-13 0Z', c.pinkLight),
    path('M9 31c-4 1-7 5-5 9 3 2 7 0 9-4l-4-5Z', c.cream),
  ],
  pork: [
    ellipse(25, 27, 15, 10, c.pink),
    circle(38, 24, 7, c.pinkLight),
    ellipse(44, 26, 3.5, 2.8, c.pinkDark),
    path('M34 18 36 11l6 7Z', c.pinkDark),
    path('M14 34v9h5l2-8m13-1 1 9h5l-1-11', 'none', { stroke: c.pinkDark, 'stroke-width': 3.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    path('M11 24C4 19 4 29 9 27c3-1 2-5-1-5', 'none', { stroke: c.pinkDark, 'stroke-width': 2, 'stroke-linecap': 'round' }),
    circle(40, 23, 1, c.brownDark),
  ],
  beef: [
    path('M14 17c7-5 21-5 28 1l-1 17H15c-5-4-6-12-1-18Z', c.brown),
    path('M7 18c2-4 7-6 11-3l2 8-5 8H8c-3-3-4-9-1-13Z', c.brownDark),
    path('M7 18 3 13c4-1 7 1 8 5m7-3 4-5c2 3 1 6-2 8', 'none', { stroke: c.creamDark, 'stroke-width': 2.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    path('M17 32v11h4l2-10m13 0 1 10h4l-1-12', 'none', { stroke: c.brownDark, 'stroke-width': 3.5, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }),
    path('M41 20c5 4 5 10 2 14l3 3', 'none', { stroke: c.brownDark, 'stroke-width': 2.2, 'stroke-linecap': 'round' }),
    path('M25 17c4 0 8 1 11 4-4 1-7 4-8 9-4-2-6-7-3-13Z', c.cream),
    ellipse(9, 27, 4, 2.5, c.tanLight),
    circle(11, 20, 1, c.creamLight),
  ],
  lamb: [
    path('M15 17c1-5 7-7 11-4 4-4 10-1 10 3 5-1 9 3 7 7 4 3 1 9-3 10-3 5-9 5-12 2-4 3-9 0-9-4-5-1-8-6-4-10Z', c.cream),
    path('M7 19c3-4 8-5 11-1l1 9-5 7H8c-4-3-4-11-1-15Z', c.brownDark),
    ellipse(8, 20, 4, 2, c.tan, { transform: 'rotate(-24 8 20)' }),
    path('M18 33v10m8-9v9m8-9v9', 'none', { stroke: c.brownDark, 'stroke-width': 3.2, 'stroke-linecap': 'round' }),
    circle(11, 22, 1, c.creamLight),
  ],
  duck: [
    ellipse(28, 31, 14, 8.5, c.orangeDark),
    path('M17 30c-4-6-4-14 0-18 3-4 7-3 9 0 2 4 0 8-3 11l-1 8-5-1Z', c.orange),
    circle(21, 11, 6, c.orange),
    path('M16 10 7 13l9 3c2-1 2-4 0-6Z', c.yellowDark),
    path('M22 28c5-5 12-4 17 1-5 1-9 4-11 8-4-1-7-5-6-9Z', c.orangeLight),
    path('M24 38v5m8-5v5m-11 0h6m2 0h7', 'none', { stroke: c.orangeDark, 'stroke-width': 2.5, 'stroke-linecap': 'round' }),
    circle(22, 10, 1, c.brownDark),
  ],
  fish: [
    path('M5 24C13 13 28 11 39 19l8-8-2 13 2 13-8-8C28 37 13 35 5 24Z', c.fish),
    path('M8 22c8-7 19-9 28-4-7 1-13 7-17 15-5-2-9-5-11-11Z', c.fishLight),
    circle(13, 21, 2, c.creamLight), circle(13, 21, 0.9, c.fishDark),
    path('M18 18c-2 4-2 9 0 13', 'none', { stroke: c.fishDark, 'stroke-width': 1.6, 'stroke-linecap': 'round' }),
    path('M24 15c1-5 5-8 9-8 1 4-1 7-5 9l-4-1Zm0 18c2 5 6 7 10 6 0-4-2-7-6-8l-4 2Z', c.fishDark),
  ],
  shrimp: [
    path('M38 12C27 4 13 11 9 23c-4 11 4 21 15 21 8 0 15-5 18-12-5 4-11 5-16 2-6-3-7-10-2-15 4-4 10-4 14 0l0-7Z', c.orange),
    path('M35 12c-8-3-17 1-20 9-3 8 2 15 10 16-5-3-7-8-4-13 3-6 9-8 15-5l-1-7Z', c.orangeLight),
    path('M13 25c5 2 10 5 13 10m-8-17c4 3 8 7 10 12m-4-18c3 3 6 7 7 11', 'none', { stroke: c.orangeDark, 'stroke-width': 1.7, 'stroke-linecap': 'round' }),
    circle(36, 15, 1.4, c.brownDark),
  ],
  crab: [
    ellipse(24, 29, 13, 10, c.red),
    path('M12 28C5 28 1 24 3 19c5 0 9 3 11 8l-2 1Zm24 0c7 0 11-4 9-9-5 0-9 3-11 8l2 1Z', c.redLight),
    path('M9 20 4 14m8 9 2-9m25 6 5-6m-8 9-2-9M13 35l-7 5m12-3-3 7m20-9 7 5m-12-3 3 7', 'none', { stroke: c.redDark, 'stroke-width': 3, 'stroke-linecap': 'round' }),
    circle(19, 26, 1.6, c.creamLight), circle(29, 26, 1.6, c.creamLight),
    line(21, 34, 27, 34, c.redDark, 1.5),
  ],
} satisfies FoodIconDefinitionMap
