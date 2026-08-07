import { palette as c } from './palette'
import { circle, ellipse, line, path, polyline, rect } from './primitives'
import type { FoodIconDefinitionMap } from './types'

export const vegetableIconDefinitions = {
  spinach: [
    path('M24 4C14 8 9 16 11 25c2 9 8 14 13 18 6-4 12-11 13-20C38 14 32 7 24 4Z', c.leaf),
    path('M24 5c-6 5-9 12-8 21 1 5 3 9 6 13-1-10 0-23 2-34Z', c.leafLight),
    line(24, 13, 24, 43, c.leafDark, 2),
  ],
  broccoli: [
    path('M19 24h11l5 18H14l5-18Z', c.leafLight),
    path('M23 22h5l2 20h-8l1-20Z', c.leaf),
    circle(16, 20, 8, c.leaf), circle(25, 15, 10, c.leafLight), circle(34, 21, 8, c.leaf),
    circle(24, 20, 8, c.leafDark),
  ],
  carrots: [
    path('M13 15c3-2 8-1 11 2l-7 25c-.4 1.5-2.4 1.7-3.1.3L6 20c-1-3 3-5 7-5Z', c.orange),
    path('M26 18c3-3 9-2 12 1l-3 22c-.2 1.6-2.2 2.1-3.1.8L20 23c-2-3 2-5 6-5Z', c.orangeLight),
    path('M12 17C7 13 7 8 9 5c4 2 6 5 5 10 1-6 5-9 9-9 0 5-3 9-8 11H12Zm15 2c-2-5 0-10 4-13 3 4 3 8 0 12 3-4 7-5 10-3-2 4-7 6-12 6l-2-2Z', c.leaf),
  ],
  tomatoes: [
    circle(18, 27, 13, c.red), circle(32, 28, 10, c.redLight),
    path('M18 12l2 6 7-2-5 5 4 4-7-2-5 5 1-7-7-2 7-2 3-5Zm14 6 1 5 5-1-4 4 3 3-5-1-4 3 1-5-4-3 5 1 2-4Z', c.leafDark),
    ellipse(13, 24, 3, 5, c.redLight),
  ],
  onion: [
    path('M24 9c8 7 14 13 14 22 0 8-6 13-14 13S10 39 10 31c0-9 6-15 14-22Z', c.tanLight),
    path('M24 10c-2 10-3 22 1 34-8 .5-13-5-13-13 0-8 5-14 12-21Z', c.cream),
    path('M22 10c-1-4 0-7 3-9 2 3 2 6 0 9h-3Z', c.leafDark),
    line(18, 41, 14, 45, c.brown, 1.7), line(24, 43, 24, 47, c.brown, 1.7), line(30, 41, 34, 45, c.brown, 1.7),
  ],
  garlic: [
    path('M24 9c3 5 4 8 4 11 6-2 12 3 12 10 0 9-7 14-16 14S8 39 8 30c0-7 6-12 12-10 0-3 1-7 4-11Z', c.cream),
    path('M24 17c-3 7-3 18 0 27-5 0-8-6-8-14 0-6 3-10 8-13Z', c.creamLight),
    path('M23 10c-1-4 0-7 3-9 2 3 2 6 0 10l-3-1Z', c.leafDark),
    polyline('16,25 18,38 24,44 30,38 32,25', c.creamDark, 1.4),
  ],
  mushrooms: [
    path('M30 7c6 0 10 4 10 9H20c0-5 4-9 10-9Z', c.brown),
    path('M27 16h7l-1 10h-5l-1-10Z', c.cream),
    path('M15 15c8 0 14 5 14 11H1c0-6 6-11 14-11Z', c.tan),
    path('M9 26h12l-2 15H12L9 26Z', c.creamLight),
    path('M7 21c5-5 12-5 17 0-6-2-11-1-17 0Z', c.tanLight),
  ],
  'frozen-peas': [
    rect(8, 7, 32, 36, 7, c.leaf), rect(8, 7, 32, 9, 5, c.leafLight),
    path('M8 30c7-5 14-5 21-1 4 2 8 2 11 0v14H8V30Z', c.leafDark),
    circle(16, 27, 4, c.limeLight), circle(25, 31, 4, c.limeLight), circle(33, 25, 4, c.limeLight), circle(33, 36, 3, c.limeLight),
  ],
  potato: [
    path('M8 26C8 15 17 7 29 9c10 1 15 9 12 20-2 10-10 16-21 14C12 42 7 35 8 26Z', c.tan),
    path('M12 23c2-7 8-11 15-11-7 4-10 12-9 23-4-2-7-6-6-12Z', c.tanLight),
    circle(29, 18, 1.7, c.brown), circle(34, 30, 1.8, c.brown), circle(20, 35, 1.4, c.brown),
  ],
  'sweet-potato': [
    path('M6 27C8 17 17 11 27 9c9-2 16 3 15 11-1 10-13 21-24 22C9 43 4 36 6 27Z', c.purple),
    path('M10 25c4-7 10-11 18-13-7 5-11 12-12 24-4-2-7-6-6-11Z', c.purpleLight),
    ellipse(34, 17, 5, 4, c.yellowLight, { transform: 'rotate(-24 34 17)' }),
  ],
  'white-radish': [
    path('M17 16c7-2 15 1 17 7 2 7-4 16-14 22 1-7-2-9-6-14-5-7-3-13 3-15Z', c.white),
    path('M18 17c-4 8-2 16 5 24-2 2-4 3-6 4 1-7-2-9-6-14-4-7 0-12 7-14Z', c.creamDark),
    path('M18 17C10 16 7 11 8 5c6 1 10 5 11 10 0-7 4-12 9-14 2 6-1 12-8 16h-2Zm5 1c3-6 9-8 14-6-2 5-7 8-14 8v-2Z', c.leaf),
  ],
  'lotus-root': [
    path('M10 31 29 8c3-4 9-4 12 0 3 3 3 8 0 12L22 43 10 31Z', c.tan),
    ellipse(15, 36, 10, 8, c.creamLight, { transform: 'rotate(38 15 36)' }),
    circle(15, 36, 2.1, c.tan), circle(10, 35, 1.5, c.tan), circle(19, 33, 1.5, c.tan), circle(18, 40, 1.5, c.tan), circle(12, 40, 1.5, c.tan),
  ],
  'chinese-yam': [
    path('M12 42c-4-2-5-7-2-11L29 6c3-4 9-3 11 1 2 3 1 6-1 9L19 40c-2 3-5 4-7 2Z', c.tan),
    path('M12 35 33 8c1-1 3-2 5-1-4 2-7 6-10 11L16 38c-2 2-4 1-4-3Z', c.tanLight),
    circle(21, 29, 1.3, c.brown), circle(29, 19, 1.2, c.brown), circle(15, 37, 1.1, c.brown),
  ],
  'chinese-cabbage': [
    path('M24 5c10 3 16 11 15 22-1 10-6 16-15 17-9-1-14-7-15-17C8 16 14 8 24 5Z', c.leafLight),
    path('M24 8c-6 7-8 18-5 34-6-3-9-9-9-16 0-8 5-15 14-18Zm0 0c7 8 8 20 5 34 6-3 9-9 9-16 0-8-5-15-14-18Z', c.leaf),
    path('M22 16h4l3 26H19l3-26Z', c.creamLight),
  ],
  'baby-cabbage': [
    path('M24 8c8 3 13 10 12 20-1 8-5 13-12 16-7-3-11-8-12-16-1-10 4-17 12-20Z', c.limeLight),
    path('M24 10c-5 8-6 20-3 33-5-3-7-8-7-15 0-8 3-14 10-18Zm0 0c5 8 6 20 3 33 5-3 7-8 7-15 0-8-3-14-10-18Z', c.leafLight),
    path('M22 18h4l2 25h-8l2-25Z', c.creamLight),
  ],
  'bok-choy': [
    path('M20 23c-8-4-11-11-8-18 8 2 12 9 12 18h-4Zm8 0c0-9 4-16 12-18 3 8-1 15-9 19l-3-1Zm-4-2C17 16 16 9 20 3c6 5 8 12 5 20l-1-2Z', c.leaf),
    path('M16 20c2 1 5 3 8 7 3-4 6-6 9-8l4 20c-7 6-19 6-26 0l5-19Z', c.creamLight),
    path('M24 25v18M16 22l8 20m9-21-9 21', 'none', { stroke: c.leafLight, 'stroke-width': 2.4, 'stroke-linecap': 'round' }),
  ],
  lettuce: [
    path('M24 6c5-4 10 0 10 5 6-2 11 4 8 9 6 3 4 11-1 13 1 7-7 11-12 8-4 6-13 2-13-3-7 1-11-7-7-12-5-4-1-11 5-12-2-6 5-11 11-8Z', c.leafLight),
    path('M24 13c8-3 14 4 11 11 5 4 0 12-6 10-3 7-12 4-11-2-7 0-8-9-2-12-2-5 3-9 8-7Z', c.leaf),
    polyline('15,30 23,24 31,29 24,38', c.leafDark, 1.5),
  ],
  'chinese-leaf-lettuce': [
    path('M13 43C7 29 9 14 17 5c4 11 3 24 0 38h-4Zm10 0C18 27 20 11 26 3c6 11 5 26 2 40h-5Zm10 0c-2-13 0-26 8-33 2 12-1 24-5 33h-3Z', c.leaf),
    path('M16 42c-2-12 0-23 3-31 0 11 2 21 1 31h-4Zm10 0c-1-12 1-24 4-32-1 12 1 23 0 32h-4Z', c.leafLight),
  ],
  cabbage: [
    circle(24, 25, 18, c.leafLight),
    path('M8 25c7-8 15-11 16-18 2 7 10 10 16 18-6-2-11 0-16 8-5-8-10-10-16-8Z', c.leaf),
    path('M24 8c-5 9-5 22 0 34m0-9c-6 0-11 2-15 6m15-6c6 0 11 2 15 6', 'none', { stroke: c.leafDark, 'stroke-width': 1.8, 'stroke-linecap': 'round' }),
  ],
  celery: [
    path('M13 44 17 17h5l-2 27h-7Zm9 0 1-30h5l1 30h-7Zm8 0-1-25h5l4 25h-8Z', c.limeLight),
    path('M17 18C10 16 7 10 10 5c6 1 10 6 10 12l-3 1Zm8-3c-2-7 1-12 7-14 3 6 0 12-5 16l-2-2Zm6 5c3-6 9-8 14-5-2 6-7 9-13 8l-1-3Z', c.leaf),
    line(13, 44, 38, 44, c.leafDark, 2),
  ],
  celtuce: [
    path('M18 44 20 12h12l2 32H18Z', c.limeLight),
    path('M26 13h6l2 31h-8V13Z', c.leafLight),
    path('M22 15C13 15 8 10 9 4c7 0 12 4 14 10l-1 1Zm8 3c2-8 8-12 14-10-1 7-6 11-14 12v-2Zm-9 8c-7 0-11-3-12-8 6-1 10 1 13 6l-1 2Z', c.leaf),
  ],
  cucumber: [
    path('M8 36C3 31 5 24 10 18L23 6c6-5 14-3 17 2 3 5 1 11-4 16L22 38c-5 5-10 3-14-2Z', c.leaf),
    path('M10 31c2-6 8-13 16-20 4-4 9-5 13-2-6 0-11 4-16 9L12 35c-1-1-2-2-2-4Z', c.leafLight),
    circle(15, 30, 1.2, c.leafDark), circle(25, 20, 1.2, c.leafDark), circle(33, 13, 1.2, c.leafDark),
  ],
  eggplant: [
    path('M16 15c9-4 21 1 24 10 3 10-5 18-16 18S7 37 9 28c1-5 3-9 7-13Z', c.purple),
    path('M13 25c4-6 11-9 19-6-7 1-13 8-14 18-4-2-7-7-5-12Z', c.purpleLight),
    path('M17 16c-2-6 3-11 9-11 0 4-1 6-4 9 5-2 9-1 12 2-5 4-11 4-17 0Z', c.leafDark),
  ],
  'green-pepper': [
    path('M24 12c9-4 17 3 17 14 0 12-7 18-17 18S7 38 7 26c0-11 8-18 17-14Z', c.leaf),
    path('M13 24c1-7 5-11 11-11-4 6-5 16-2 28-7-1-10-8-9-17Z', c.leafLight),
    path('M22 13c-2-6 0-10 5-12 2 4 1 8-1 12h-4Z', c.leafDark),
    path('M22 14c2 5 2 20 0 27m3-27c5 8 6 19 3 27', 'none', { stroke: c.leafDark, 'stroke-width': 1.5, 'stroke-linecap': 'round' }),
  ],
  cauliflower: [
    path('M12 27 5 41c8 2 14 0 19-6 5 6 11 8 19 6l-7-14H12Z', c.leaf),
    circle(14, 22, 8, c.cream), circle(23, 14, 10, c.creamLight), circle(34, 21, 8, c.cream), circle(24, 25, 10, c.creamLight),
    circle(23, 14, 3, c.creamDark), circle(14, 22, 2.4, c.creamDark), circle(32, 22, 2.5, c.creamDark),
  ],
  pumpkin: [
    ellipse(24, 27, 19, 16, c.orange),
    ellipse(17, 27, 8, 15, c.orangeLight), ellipse(31, 27, 8, 15, c.orangeDark),
    path('M22 12c-1-6 2-10 7-10 1 5-1 9-5 12l-2-2Z', c.leafDark),
    line(24, 13, 24, 42, c.orangeDark, 1.4),
  ],
  'winter-melon': [
    path('M7 31C3 22 11 12 24 8c11-3 19 2 19 11 0 10-11 20-22 23C14 44 9 39 7 31Z', c.leafDark),
    path('M10 28c3-8 12-14 22-16-8 4-14 12-16 24-3-1-5-4-6-8Z', c.leafLight),
    path('M17 35c7 0 14-4 20-11', 'none', { stroke: c.creamLight, 'stroke-width': 1.5, 'stroke-linecap': 'round', opacity: 0.8 }),
  ],
  'green-beans': [
    path('M9 11c14 2 23 11 26 26', 'none', { stroke: c.leaf, 'stroke-width': 5, 'stroke-linecap': 'round' }),
    path('M14 7c13 4 21 15 22 31', 'none', { stroke: c.leafLight, 'stroke-width': 4, 'stroke-linecap': 'round' }),
    path('M7 16c12 5 18 14 18 26', 'none', { stroke: c.leafDark, 'stroke-width': 4, 'stroke-linecap': 'round' }),
  ],
  shiitake: [
    path('M24 8c10 0 18 7 18 16H6c0-9 8-16 18-16Z', c.brown),
    path('M10 23c7-5 21-5 28 0-4 5-10 7-14 7s-10-2-14-7Z', c.cream),
    path('M19 28h10l-2 15h-6l-2-15Z', c.creamLight),
    path('M17 13l3 4m8-5-2 5m8 0-4 3', 'none', { stroke: c.tanLight, 'stroke-width': 1.8, 'stroke-linecap': 'round' }),
  ],
  enoki: [
    rect(10, 19, 5, 24, 2.5, c.cream), rect(17, 13, 5, 30, 2.5, c.creamLight), rect(24, 17, 5, 26, 2.5, c.cream), rect(31, 11, 5, 32, 2.5, c.creamLight),
    circle(12.5, 17, 4.5, c.tanLight), circle(19.5, 11, 4.5, c.tan), circle(26.5, 15, 4.5, c.tanLight), circle(33.5, 9, 4.5, c.tan),
    path('M9 38c8 3 21 3 29 0v6H9v-6Z', c.creamDark),
  ],
  ginger: [
    path('M7 28c1-6 6-10 12-8-2-7 4-13 10-10 4 2 5 6 3 10 7-3 14 2 13 9-1 6-7 9-13 7-2 7-11 9-15 4-6-1-8-8-5-14-7-1-12-5-11-10Z', c.tan),
    path('M10 27c3-4 7-5 12-3-1-5 2-9 7-11-3 4-3 10 2 15-8-2-14 2-16 9-4-2-6-6-5-10Z', c.tanLight),
    circle(29, 16, 1.4, c.brown), circle(34, 30, 1.4, c.brown), circle(18, 33, 1.2, c.brown),
  ],
  scallion: [
    path('M12 44 16 17h6l-2 27h-8Zm9 0 2-32h6l-1 32h-7Zm10 0-2-28h6l5 28h-9Z', c.creamLight),
    path('M16 18 18 3h5l-1 15h-6Zm7-5 3-11h5l-2 15-6-4Zm7 5 5-14h5l-5 17-5-3Z', c.leaf),
    path('M12 39c8 2 18 2 28 0v5H12v-5Z', c.leafLight),
  ],
  chives: [
    path('M11 42 15 5m1 37 4-39m1 39 4-36m1 36 4-38m1 38 3-32m2 32 2-35', 'none', { stroke: c.leaf, 'stroke-width': 3, 'stroke-linecap': 'round' }),
    path('M9 31c10 3 20 3 31 0l-1 7c-10 2-19 2-29 0l-1-7Z', c.yellow),
    line(13, 34, 36, 34, c.yellowDark, 1.4),
  ],
  zucchini: [
    path('M7 35C4 29 8 23 14 18L30 6c6-4 12 0 12 6 0 5-4 10-9 14L18 39c-5 4-9 1-11-4Z', c.leafDark),
    path('M10 31c4-6 12-13 22-21 3-2 6-3 9-1-6 2-11 7-16 12L12 36c-1-1-2-3-2-5Z', c.leafLight),
    ellipse(35, 10, 6, 4, c.creamLight, { transform: 'rotate(-34 35 10)' }),
  ],
  loofah: [
    path('M8 36C3 30 7 22 13 17L29 5c6-4 13 0 13 6 0 6-5 11-10 15L18 40c-4 4-8 1-10-4Z', c.lime),
    path('M10 31c5-6 13-13 23-21 3-2 6-2 8 0-7 3-12 8-17 13L12 36c-1-2-2-3-2-5Z', c.limeLight),
    polyline('13,31 17,32 18,27 23,28 24,23 29,24 30,19 35,20', c.leafDark, 1.5),
  ],
  'bitter-melon': [
    path('M8 36C4 30 7 23 13 18L28 7c6-4 13 0 13 6 0 5-4 10-9 14L18 40c-4 4-8 1-10-4Z', c.leaf),
    path('M11 31c4-6 11-12 20-19 3-2 6-2 9 0-6 3-11 8-16 13L12 36c-1-1-2-3-1-5Z', c.leafLight),
    circle(14, 30, 1.8, c.leafDark), circle(19, 24, 1.8, c.leafDark), circle(25, 20, 1.8, c.leafDark), circle(31, 14, 1.8, c.leafDark), circle(27, 29, 1.8, c.leafDark), circle(35, 20, 1.8, c.leafDark),
  ],
  corn: [
    path('M24 6c8 0 13 8 13 19 0 12-5 19-13 19s-13-7-13-19C11 14 16 6 24 6Z', c.yellow),
    path('M24 7c-4 7-5 22-2 36-6-2-9-9-9-18 0-10 4-17 11-18Z', c.yellowLight),
    path('M12 20C6 25 7 37 15 44c-1-9 2-17 9-24-5 3-9 3-12 0Zm24 0c6 5 5 17-3 24 1-9-2-17-9-24 5 3 9 3 12 0Z', c.leaf),
    path('M17 18h14M15 25h18M15 32h18M20 9l-2 33m8-34 2 34', 'none', { stroke: c.yellowDark, 'stroke-width': 1.2, opacity: 0.75 }),
  ],
  'bean-sprouts': [
    path('M9 41c0-9 7-13 9-20m1 21c-1-9 6-15 9-24m2 24c6-7 7-14 4-20m-17 18c8 3 16 3 22-1', 'none', { stroke: c.cream, 'stroke-width': 3.2, 'stroke-linecap': 'round' }),
    ellipse(19, 18, 4.5, 3, c.yellowLight, { transform: 'rotate(-28 19 18)' }),
    ellipse(29, 16, 4.5, 3, c.yellow, { transform: 'rotate(24 29 16)' }),
    ellipse(35, 20, 4.2, 2.8, c.yellowLight, { transform: 'rotate(42 35 20)' }),
  ],
} satisfies FoodIconDefinitionMap
