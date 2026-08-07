# Food Token Recognition Fixes Design

## Context

The first complete Food Token board exposed four recognition failures: `lamb` and `duck` looked like generic meat cuts, the `fish` eye was placed at the tail end, and the compatibility-only `pasta` icon looked like an unexplained package.

## Approved direction

- Use original animal silhouettes for meat concepts that otherwise collapse into generic cuts.
- Keep `chicken-breast` and `chicken-thigh` unchanged because their cut silhouettes are already distinctive.
- Render `pork` as a side-profile pig with a short snout, round body, and curled tail.
- Render `beef` as a side-profile cow with a broad body, horns, and tail.
- Render `lamb` as a side-profile sheep with a woolly cream body and darker face and legs.
- Render `duck` as a side-profile duck with a flat bill, long neck, and webbed feet.
- Render `fish` with its head, eye, and gill on the left and its tail on the right.
- Render `pasta` as a slightly angled tied bundle of dry spaghetti without packaging or utensils.

## Visual contract

All replacements keep the existing `48 × 48` transparent-canvas Bold Pantry contract: a strong rounded silhouette, two or three dominant fills, top-left light, bottom-right shade, no background badge, no text, and no decorative scene. Animal icons remain ingredient identifiers rather than mascots: no facial expression, clothing, or anthropomorphic pose.

## Compatibility

The existing visual keys and registry API remain unchanged. No FoodDefinition, preset, localization, or inventory data is migrated. The correction is limited to SVG definitions in the category catalog.

## Verification

- Add a focused browser contract that exposes the corrected keys in the developer size ramp.
- Confirm the contract fails before the size-ramp update and passes afterward.
- Inspect all corrected icons at 24, 32, 48, and 64 px on the real developer board.
- Run frontend lint, typecheck, production build, and the full mobile/desktop Playwright suite.
