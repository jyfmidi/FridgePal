import type { Component } from 'vue'
import IconBroccoli from './IconBroccoli.vue'
import IconCarrots from './IconCarrots.vue'
import IconChickenBreast from './IconChickenBreast.vue'
import IconEggs from './IconEggs.vue'
import IconFrozenPeas from './IconFrozenPeas.vue'
import IconGarlic from './IconGarlic.vue'
import IconLemon from './IconLemon.vue'
import IconMilk from './IconMilk.vue'
import IconMushrooms from './IconMushrooms.vue'
import IconOnion from './IconOnion.vue'
import IconPasta from './IconPasta.vue'
import IconRice from './IconRice.vue'
import IconSpinach from './IconSpinach.vue'
import IconTofu from './IconTofu.vue'
import IconTomatoes from './IconTomatoes.vue'
import IconYogurt from './IconYogurt.vue'

/**
 * Food Token icon registry (UI-CMP-01).
 *
 * One coherent family: 48x48 viewBox, semi-flat full color, bold silhouette,
 * 2-3 fills per asset, shared top-left light with a bottom-right shade.
 * Fill-based (never outline-only) so tokens stay legible on light tiles
 * and on the neutral selection tray. Registry is keyed and statically imported,
 * so bundlers can tree-shake unused icons.
 */
export const foodIcons: Record<string, Component> = {
  'chicken-breast': IconChickenBreast,
  spinach: IconSpinach,
  mushrooms: IconMushrooms,
  broccoli: IconBroccoli,
  tofu: IconTofu,
  yogurt: IconYogurt,
  lemon: IconLemon,
  eggs: IconEggs,
  milk: IconMilk,
  carrots: IconCarrots,
  tomatoes: IconTomatoes,
  onion: IconOnion,
  garlic: IconGarlic,
  rice: IconRice,
  pasta: IconPasta,
  'frozen-peas': IconFrozenPeas,
}
