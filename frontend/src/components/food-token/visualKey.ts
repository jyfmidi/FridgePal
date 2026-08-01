/**
 * Food Token visual resolution (UI-CMP-01).
 *
 * A food's icon is resolved in this priority order:
 *   1. an admin-uploaded custom icon (data URI, rendered through `<img>`);
 *   2. the curated Food Token key from the food's `visual_key` (or the
 *      admin-assigned override);
 *   3. a deterministic monogram of the localized name.
 *
 * Every surface renders tokens from the canonical `foodKey`; this registry
 * carries the server-provided mappings so the chosen icon renders consistently
 * in Storage, Rescue, match belts, Recipe Editor, Recipes, and reconciliation
 * without touching every call site.
 */

const visualKeyOverrides = new Map<string, string>()
const customIcons = new Map<string, string>()

export function registerVisualKey(foodKey: string, visualKey: string): void {
  if (visualKey && visualKey !== foodKey) {
    visualKeyOverrides.set(foodKey, visualKey)
  }
}

export function visualKeyFor(foodKey: string): string {
  return visualKeyOverrides.get(foodKey) ?? foodKey
}

/** Registers an admin-uploaded icon data URI for a food. */
export function registerCustomIcon(foodKey: string, dataUri: string): void {
  if (dataUri) {
    customIcons.set(foodKey, dataUri)
  }
}

export function customIconFor(foodKey: string): string | undefined {
  return customIcons.get(foodKey)
}
