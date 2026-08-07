import { palette as c } from './palette'
import { circle, ellipse, line, path, polygon } from './primitives'
import type { FoodIconDefinitionMap } from './types'

export const fruitIconDefinitions = {
  apple: [
    path('M24 14c8-7 18-2 18 10 0 12-8 20-18 20S6 36 6 24c0-12 10-17 18-10Z', c.red),
    path('M11 23c1-7 6-11 12-9-5 5-6 15-3 25-6-2-10-8-9-16Z', c.redLight),
    path('M24 14c-2-6 0-10 5-13 2 5 0 9-3 13h-2Z', c.brownDark),
    path('M28 9c5-5 10-4 13 0-4 4-8 5-13 2V9Z', c.leaf),
  ],
  banana: [
    path('M7 17c9 10 20 14 31 7 3-2 7 2 5 6C35 44 16 45 7 30c-3-5-3-10 0-13Z', c.yellow),
    path('M8 20c8 12 21 17 34 7-6 12-20 16-30 7-4-4-6-9-4-14Z', c.yellowLight),
    path('M6 18c-2-3 0-7 4-7 2 2 2 5 0 8l-4-1Zm32 7c1-4 5-5 8-3 1 4-1 7-5 8l-3-5Z', c.yellowDark),
  ],
  orange: [
    circle(24, 27, 17, c.orange),
    path('M12 24c2-8 7-13 15-14-6 5-8 16-5 31-7-1-11-8-10-17Z', c.orangeLight),
    path('M24 10c-1-5 2-8 6-9 1 4-1 7-4 10l-2-1Z', c.leafDark),
    path('M28 8c5-4 10-2 11 2-4 3-8 3-12 0l1-2Z', c.leaf),
  ],
  mandarin: [
    ellipse(24, 29, 18, 14, c.orangeLight),
    path('M8 28c4-8 10-12 16-13-4 6-5 15-2 27-8-1-13-6-14-14Z', c.orange),
    path('M21 15c1-5 5-7 9-5 0 4-2 6-6 7l-3-2Z', c.leafDark),
    path('M26 14c5-5 11-3 12 2-5 2-8 2-12 0v-2Z', c.leaf),
    path('M15 23c6 3 12 3 18 0M14 31c7 3 13 3 20 0', 'none', { stroke: c.orangeDark, 'stroke-width': 1.2, opacity: 0.7 }),
  ],
  pear: [
    path('M24 8c6 0 9 5 8 11 7 5 11 11 9 17-2 7-9 10-17 10S9 43 7 36c-2-6 2-12 9-17-1-6 2-11 8-11Z', c.limeLight),
    path('M11 34c0-7 5-12 11-16-2-4-1-7 2-10-5 2-7 6-5 12-6 4-9 9-8 14Z', c.yellowLight),
    path('M24 9c-1-5 1-8 5-10 2 4 0 8-3 11l-2-1Z', c.brownDark),
    path('M29 6c5-3 9-1 10 3-4 2-7 2-10 0V6Z', c.leaf),
  ],
  grapes: [
    circle(17, 20, 6, c.purpleLight), circle(25, 18, 6, c.purple), circle(33, 21, 6, c.purpleDark),
    circle(13, 28, 6, c.purple), circle(22, 27, 6, c.purpleLight), circle(31, 29, 6, c.purple), circle(38, 28, 5, c.purpleLight),
    circle(18, 36, 6, c.purpleDark), circle(27, 36, 6, c.purple), circle(34, 38, 5, c.purpleLight), circle(25, 43, 4, c.purpleDark),
    path('M25 14c-2-7 1-11 6-13 2 5 0 9-4 13h-2Z', c.leafDark),
    path('M25 13C15 11 11 6 13 1c7 1 12 5 14 11l-2 1Z', c.leaf),
  ],
  watermelon: [
    path('M5 38 20 7c2-4 7-5 10-1l15 27c2 4-1 9-6 9H9c-3 0-5-2-4-4Z', c.leafDark),
    path('M9 36 23 9c1-2 4-2 5 0l14 25c1 2 0 4-3 4H11c-2 0-3-1-2-2Z', c.red),
    path('M9 36h32c0 2-1 3-3 3H12c-2 0-3-1-3-3Z', c.creamLight),
    ellipse(21, 23, 1.4, 3, c.brownDark, { transform: 'rotate(-18 21 23)' }), ellipse(30, 21, 1.4, 3, c.brownDark, { transform: 'rotate(18 30 21)' }), ellipse(27, 30, 1.4, 3, c.brownDark),
  ],
  cantaloupe: [
    ellipse(24, 25, 18, 19, c.tanLight),
    path('M9 23c3-9 9-15 17-17-6 6-8 18-4 37-8-1-13-9-13-20Z', c.yellowLight),
    path('M8 19c10 4 22 4 32 0M7 28c11 4 23 4 34 0M10 36c9 3 19 3 28 0M17 8c-3 11-3 24 1 34M29 7c4 11 4 24 1 35', 'none', { stroke: c.cream, 'stroke-width': 1.2, opacity: 0.9 }),
    path('M23 6c-1-4 2-7 6-7 1 4-1 7-4 8l-2-1Z', c.leafDark),
  ],
  strawberry: [
    path('M24 12c10 0 16 6 14 15-2 9-9 15-14 19-5-4-12-10-14-19-2-9 4-15 14-15Z', c.red),
    path('M15 24c1-6 5-10 11-11-4 6-5 15-1 27-5-4-9-9-10-16Z', c.redLight),
    path('M24 14c-7 2-12-1-14-6 5-2 9-1 13 3 0-6 4-10 9-11 1 5-1 9-5 12 5-3 10-2 13 2-4 4-10 4-16 0Z', c.leaf),
    ellipse(20, 23, 1, 2, c.yellowLight), ellipse(29, 23, 1, 2, c.yellowLight), ellipse(24, 31, 1, 2, c.yellowLight), ellipse(19, 34, 1, 2, c.yellowLight), ellipse(30, 34, 1, 2, c.yellowLight),
  ],
  blueberries: [
    circle(17, 30, 12, c.fish), circle(31, 29, 12, c.purple), circle(25, 17, 11, c.fishLight),
    path('M25 9l2 5 5-2-3 4 4 3-5 1v5l-3-4-4 3 1-5-5-1 5-2-3-4 5 2 1-5Z', c.fishDark),
    path('M16 21l2 4 4-1-3 3 3 3-4-1-1 4-2-4-4 1 3-3-3-3 4 1 1-4Z', c.fishDark),
    path('M31 20l2 4 4-1-3 3 3 3-4-1-1 4-2-4-4 1 3-3-3-3 4 1 1-4Z', c.purpleDark),
  ],
  peach: [
    path('M24 12c8-7 19-1 19 11 0 12-9 21-19 21S5 35 5 23c0-12 11-18 19-11Z', c.pink),
    path('M10 23c1-8 7-12 14-11-5 6-6 17-2 29-7-2-12-8-12-18Z', c.pinkLight),
    path('M25 12c4 7 5 17 0 28', 'none', { stroke: c.pinkDark, 'stroke-width': 1.8, 'stroke-linecap': 'round' }),
    path('M24 11c-1-5 2-9 7-10 1 5-1 8-5 11l-2-1Z', c.leafDark),
  ],
  mango: [
    path('M9 33C5 24 10 14 19 9 28 4 39 6 41 15 43 26 32 39 21 43 15 45 11 41 9 33Z', c.yellow),
    path('M12 30C12 22 17 15 24 11 19 18 19 29 23 39 18 41 13 37 12 30Z', c.yellowLight),
    path('M31 7c3-6 8-8 13-5-2 6-6 9-12 8l-1-3Z', c.leaf),
    line(31, 8, 28, 12, c.leafDark, 2),
  ],
  kiwi: [
    circle(24, 24, 19, c.brown), circle(24, 24, 15, c.lime), circle(24, 24, 5, c.creamLight),
    ellipse(24, 12, 1, 2.2, c.brownDark), ellipse(32, 15, 1, 2.2, c.brownDark, { transform: 'rotate(45 32 15)' }), ellipse(36, 24, 1, 2.2, c.brownDark, { transform: 'rotate(90 36 24)' }), ellipse(32, 33, 1, 2.2, c.brownDark, { transform: 'rotate(135 32 33)' }), ellipse(24, 36, 1, 2.2, c.brownDark), ellipse(16, 33, 1, 2.2, c.brownDark, { transform: 'rotate(45 16 33)' }), ellipse(12, 24, 1, 2.2, c.brownDark, { transform: 'rotate(90 12 24)' }), ellipse(16, 15, 1, 2.2, c.brownDark, { transform: 'rotate(135 16 15)' }),
  ],
  'dragon-fruit': [
    path('M24 5c11 3 18 12 16 23-2 11-9 17-16 17S10 39 8 28C6 17 13 8 24 5Z', c.pink),
    path('M24 10c8 3 12 10 11 18-1 8-6 12-11 12S14 36 13 28c-1-8 3-15 11-18Z', c.white),
    ellipse(20, 20, 1, 2, c.brownDark, { transform: 'rotate(-25 20 20)' }), ellipse(29, 18, 1, 2, c.brownDark, { transform: 'rotate(25 29 18)' }), ellipse(18, 29, 1, 2, c.brownDark), ellipse(27, 29, 1, 2, c.brownDark, { transform: 'rotate(-25 27 29)' }), ellipse(31, 34, 1, 2, c.brownDark),
    polygon('9,20 2,15 9,13', c.leaf), polygon('39,18 46,13 40,11', c.leaf), polygon('11,35 5,39 13,40', c.leaf), polygon('36,35 43,40 34,41', c.leaf),
  ],
  pineapple: [
    path('M11 22c0-7 6-11 13-11s13 4 13 11v14c0 7-6 10-13 10s-13-3-13-10V22Z', c.yellow),
    path('M12 23c2-6 7-9 13-9-4 7-4 18 0 30-8 1-13-3-13-10V23Z', c.yellowLight),
    path('M24 13C15 10 13 5 15 1c5 2 8 5 9 10-1-6 2-10 7-12 2 5 0 10-5 14 5-5 10-5 14-2-3 4-8 6-16 5V13Z', c.leaf),
    path('M13 24h22M12 33h24M17 15l15 29M31 15 17 44', 'none', { stroke: c.yellowDark, 'stroke-width': 1.3, opacity: 0.8 }),
  ],
  pomelo: [
    path('M24 10c11 0 19 8 19 18 0 11-8 18-19 18S5 39 5 28c0-10 8-18 19-18Z', c.limeLight),
    path('M10 26c2-8 8-14 16-16-6 6-7 18-3 33-8-1-13-7-13-17Z', c.yellowLight),
    path('M23 10c-1-5 2-9 7-10 1 5-1 9-5 11l-2-1Z', c.leafDark),
    path('M29 7c5-4 10-2 12 2-4 3-8 4-13 1l1-3Z', c.leaf),
  ],
  lychee: [
    circle(17, 29, 11, c.redLight), circle(31, 29, 11, c.red), circle(24, 18, 11, c.pink),
    path('M11 26l4-2 3 3 4-2m3-10 4 2-2 4 4 2m-4 5 4-2 3 3 4-1', 'none', { stroke: c.redDark, 'stroke-width': 1.4, 'stroke-linecap': 'round' }),
    path('M24 8c-2-5 1-9 6-10 1 5-1 8-4 11l-2-1Zm4 1c7-4 12-1 13 4-5 2-9 1-13-2V9Z', c.leaf),
  ],
  lemon: [
    path('M6 27C6 17 14 9 24 8c3-5 7-5 9 0 7 3 11 9 9 17-2 10-12 18-22 17C11 41 6 35 6 27Z', c.yellow),
    path('M10 24c2-7 8-13 16-14-6 6-8 16-5 28-7-1-11-7-11-14Z', c.yellowLight),
    path('M27 8c3-6 9-8 14-5-2 6-7 9-13 8l-1-3Z', c.leaf),
  ],
} satisfies FoodIconDefinitionMap
