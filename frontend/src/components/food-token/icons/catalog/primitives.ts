import type { FoodIconAttributeValue, FoodIconElement } from './types'

type ExtraAttrs = Readonly<Record<string, FoodIconAttributeValue>>

function element(
  tag: FoodIconElement['tag'],
  attrs: Record<string, FoodIconAttributeValue>,
  extra: ExtraAttrs = {},
): FoodIconElement {
  return { tag, attrs: { ...attrs, ...extra } }
}

export function path(d: string, fill: string, extra: ExtraAttrs = {}): FoodIconElement {
  return element('path', { d, fill }, extra)
}

export function circle(cx: number, cy: number, r: number, fill: string, extra: ExtraAttrs = {}): FoodIconElement {
  return element('circle', { cx, cy, r, fill }, extra)
}

export function ellipse(
  cx: number,
  cy: number,
  rx: number,
  ry: number,
  fill: string,
  extra: ExtraAttrs = {},
): FoodIconElement {
  return element('ellipse', { cx, cy, rx, ry, fill }, extra)
}

export function rect(
  x: number,
  y: number,
  width: number,
  height: number,
  rx: number,
  fill: string,
  extra: ExtraAttrs = {},
): FoodIconElement {
  return element('rect', { x, y, width, height, rx, fill }, extra)
}

export function line(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  stroke: string,
  width = 2,
  extra: ExtraAttrs = {},
): FoodIconElement {
  return element('line', { x1, y1, x2, y2, stroke, 'stroke-width': width, 'stroke-linecap': 'round' }, extra)
}

export function polyline(points: string, stroke: string, width = 2, extra: ExtraAttrs = {}): FoodIconElement {
  return element('polyline', {
    points,
    fill: 'none',
    stroke,
    'stroke-width': width,
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
  }, extra)
}

export function polygon(points: string, fill: string, extra: ExtraAttrs = {}): FoodIconElement {
  return element('polygon', { points, fill }, extra)
}
