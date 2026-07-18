<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { foodIcons } from './icons'

/**
 * UI-CMP-01 — Food Token.
 *
 * Known `foodKey` renders the curated SVG icon; anything else renders a
 * deterministic monogram: the first user-perceived grapheme cluster of the
 * localized name on a pastel surface derived from a stable name hash.
 * The same key renders identically across Storage, Rescue, match belts,
 * Recipe Editor, Recipes, and reconciliation.
 */
const props = withDefaults(
  defineProps<{
    foodKey?: string
    /** Localized food name; also the accessible label. */
    name: string
    /** Rendered edge length in px. */
    size?: number
  }>(),
  { foodKey: undefined, size: 48 },
)

const { locale } = useI18n()

const icon = computed(() => (props.foodKey ? foodIcons[props.foodKey] : undefined))

/** First user-perceived grapheme cluster (spec 9: never byte/code-point indexing). */
function firstGrapheme(text: string, loc: string): string {
  const trimmed = text.trim()
  if (!trimmed) return '?'
  if (typeof Intl.Segmenter === 'function') {
    const segments = new Intl.Segmenter(loc, { granularity: 'grapheme' }).segment(trimmed)
    const first = segments[Symbol.iterator]().next()
    if (!first.done && first.value.segment) return first.value.segment
  }
  return Array.from(trimmed)[0] ?? '?'
}

/** Stable 32-bit FNV-1a hash; same name always lands on the same hue. */
function stableHash(text: string): number {
  let hash = 0x811c9dc5
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193)
  }
  return hash >>> 0
}

const grapheme = computed(() => firstGrapheme(props.name, locale.value).toLocaleUpperCase(locale.value))

/**
 * Hash -> harmonious HSL. Fixed saturation/lightness curve keeps the ink at
 * >= 4.5:1 against the surface for every hue (worst case verified ~6:1).
 */
const monogramStyle = computed(() => {
  const hue = stableHash(props.name.trim()) % 360
  return {
    backgroundColor: `hsl(${hue} 58% 86%)`,
    color: `hsl(${hue} 48% 24%)`,
  }
})

const boxStyle = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }))
const graphemeStyle = computed(() => ({ fontSize: `${Math.round(props.size * 0.46)}px` }))
</script>

<template>
  <span class="food-token" role="img" :aria-label="name" :style="boxStyle">
    <component :is="icon" v-if="icon" class="food-token__icon" />
    <span v-else class="food-token__monogram" :style="[monogramStyle, graphemeStyle]">{{ grapheme }}</span>
  </span>
</template>

<style scoped>
.food-token {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
}

.food-token__icon {
  width: 100%;
  height: 100%;
}

.food-token__monogram {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  border-radius: 28%;
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  user-select: none;
}
</style>
