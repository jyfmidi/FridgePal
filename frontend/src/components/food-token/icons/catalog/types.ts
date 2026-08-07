export type FoodIconTag = 'path' | 'circle' | 'ellipse' | 'rect' | 'line' | 'polyline' | 'polygon'

export type FoodIconAttributeValue = string | number

export interface FoodIconElement {
  readonly tag: FoodIconTag
  readonly attrs: Readonly<Record<string, FoodIconAttributeValue>>
}

export type FoodIconDefinition = readonly FoodIconElement[]

export type FoodIconDefinitionMap = Readonly<Record<string, FoodIconDefinition>>
