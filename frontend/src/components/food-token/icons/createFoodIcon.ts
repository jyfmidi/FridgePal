import { defineComponent, h, type Component } from 'vue'
import type { FoodIconDefinition } from './catalog/types'

export function createFoodIcon(name: string, definition: FoodIconDefinition): Component {
  return defineComponent({
    name,
    setup(_, { attrs }) {
      return () => h(
        'svg',
        {
          ...attrs,
          viewBox: '0 0 48 48',
          fill: 'none',
          xmlns: 'http://www.w3.org/2000/svg',
          'aria-hidden': 'true',
          focusable: 'false',
        },
        definition.map((item, index) => h(item.tag, { ...item.attrs, key: index })),
      )
    },
  })
}
