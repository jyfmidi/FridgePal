# Fridge Pal Food Token Icon Guide

This document is the production and reproduction guide for Fridge Pal's curated Food Token family. `UI-CMP-01` in `docs/UX_SPEC.md` remains the canonical interaction contract.

## Bold Pantry construction

- Render as deterministic code-native SVG on a `48 × 48` viewBox.
- Keep at least `4 px` clear space around the dominant silhouette.
- Fill about 70–82% of the canvas with one centered ingredient.
- Use two or three dominant flat fills. A small dark detail stroke is allowed only when it improves recognition at 24–38 px.
- Express light with one lighter top-left plane and one darker bottom-right plane.
- Prefer rounded, friendly geometry and strong outer contours.
- Do not use a background badge, plate, utensil, shelf, environment, face, text, logo, gradient, texture, cast shadow, or miniature scene.
- Use a whole ingredient plus one cut face only when the interior is the strongest identifier, such as lotus root, kiwi, watermelon, cantaloupe, or dragon fruit.
- Use generic unbranded packaging only for foods mainly recognized by their stored container: milk, yogurt, and frozen peas.
- Keep raw meat clean and abstract. Never show blood, butcher-paper scenes, loose bone fragments, or realistic marbling.
- When two raw cuts cannot remain distinct at 24 px, use a neutral side-profile source-animal silhouette instead. Keep it non-anthropomorphic and preserve specific cut icons that are already recognizable.

## Naming

- Use stable lowercase kebab-case visual keys, for example `dragon-fruit` and `white-radish`.
- Keep a visual key generic enough to reuse across localized preset aliases, but do not create vague mixed-food concepts.
- A FoodDefinition may have a precise localized name while reusing the nearest curated visual key.
- Never rename or remove a shipped visual key without a compatibility mapping because stored FoodDefinition rows may reference it.

## Approved catalog

The production registry contains the 70 approved household-food keys plus compatibility-only `rice` and `pasta`. The complete bilingual list is maintained in `docs/plans/2026-08-01-common-food-icon-library-design.md`.

## Reusable reference-generation prompt

Reference imagery can help explore a future subject pose, but it is never production-ready source art. Normalize any accepted concept into this repository's deterministic SVG catalog.

```text
Use case: logo-brand
Asset type: Fridge Pal Food Token reference icon
Primary request: Create one icon of [FOOD NAME / SUBJECT CLAUSE] for the Bold Pantry food-icon family.
Scene/backdrop: isolated object on a completely empty canvas; no environment and no enclosing badge.
Style/medium: recognition-first semi-flat vector illustration, bold friendly silhouette, rounded geometry, crisp scalable edges.
Composition/framing: centered single ingredient, 3/4 or front view chosen for instant recognition, fills 70–82% of a square canvas, at least 8% clear padding on every edge.
Lighting/mood: soft light from the top left expressed only as one simple highlight plane; one darker bottom-right shade plane.
Color palette: two or three saturated but natural food colors; strong contrast on white and warm off-white UI surfaces.
Materials/textures: flat color only; no photographic texture, grain, gloss, translucency, or realistic surface noise.
Constraints: recognizable at 24 px; no text; no logo; no watermark; no face; no plate; no utensils; no scenery; no cast shadow; no gradient; no outline-only drawing. Use at most one cut face when it is essential to recognition. Generic unbranded packaging is allowed only for milk, yogurt, or frozen peas.
Avoid: emoji styling, clay or 3D render, miniature scene, thin details, decorative leaves unrelated to the food, multiple unrelated ingredients, cyberpunk effects.
```

Replace `[FOOD NAME / SUBJECT CLAUSE]` with a concise pose description:

- `lotus-root`: a short diagonal lotus-root segment with one clean round cut face showing its radial holes.
- `bok-choy`: one compact Shanghai bok choy with a white-green bulb base and three broad dark-green leaves.
- `watermelon`: one rounded watermelon wedge with a green rind, red flesh, and three large dark seeds.
- `chicken-thigh`: one clean raw chicken thigh cut with a plump rounded silhouette and a small tapered end, without blood or realistic bone detail.
- `milk`: one generic unbranded milk carton with a single blue color band and a simple milk-drop symbol.

## Review checklist

Review every new or changed icon on both the white surface and neutral Rescue tray:

1. Recognizable without its label at 48 px.
2. Still distinct at 24 and 32 px.
3. No part clipped at the 4 px safe area.
4. No thin detail carries the identity.
5. Light foods retain contrast on white.
6. The highlight remains top-left and the shade remains bottom-right.
7. The icon uses no more than three dominant fills.
8. Similar foods differ by silhouette, pose, or cut face—not by text.
9. The same visual key renders through Storage, Rescue, recipes, History, reconciliation, and the admin picker.
10. Unknown foods still fall back to the deterministic localized monogram.
