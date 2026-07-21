# Animated Loader and Icon Clarity Design

**Date:** 2026-07-21  
**Status:** Approved  
**Scope:** Branded loading feedback and functional icon clarity in the responsive Fridge Pal client

## Goals

- Turn the existing Fridge Pal mark into a small, recognizable character during meaningful waits.
- Use a continuous playful motion without delaying usable content or making routine refreshes visually noisy.
- Make History Storage entries and other consequential actions understandable without guessing an abstract icon.
- Preserve the existing bilingual, responsive, and accessible interaction contracts.

## Loading Character

Create a reusable `FridgePalLoader` from an inline, layered version of the existing fridge mark. The loader treats the mark as the Fridge Pal character rather than as a generic progress indicator.

The default loop is a short character performance:

1. The body twists gently to one side.
2. It twists back through center to the other side.
3. It compresses slightly to anticipate a jump.
4. It hops upward by approximately 6–8 CSS pixels.
5. It lands with a small squash-and-settle response, then repeats.

The upper and lower door shapes and handles may lag the body by a few milliseconds to make the flat mark feel flexible. The silhouette must remain recognizable and the movement must not imply that the doors are opening. One loop should take approximately 1.5–1.8 seconds and repeat continuously while the loading state remains active.

Two presentation variants share the same motion:

- `page`: a centered larger character and localized status copy for initial application loading.
- `compact`: a smaller character inside an existing loading surface for longer waits such as recipe discovery.

The loader appears only after a short delay, approximately 150 milliseconds, so fast operations do not flash a loading state. Existing content remains visible wherever a refresh can safely keep stale content on screen.

For `prefers-reduced-motion: reduce`, the character is static. Loading meaning remains available through localized status text and an accessible `role="status"`; motion is never the only indicator.

## Loading Scope

Use the full page variant for the application's initial inventory hydration when no usable application content is available. Use the compact variant for recipe discovery and similarly long, blocking operations. Do not replace every small inline pending state, button submission label, or skeleton with the animated character.

This preserves `NFR-PERF-003` and keeps Storage and History refreshes calm while still giving distinctive feedback during waits that users notice.

## Functional Icon System

Keep `AppIcon` as the shared 24-by-24 line-icon system. Normalize new and corrected paths to the existing rounded line treatment, approximately 1.9 stroke width, and pair consequential icons with localized labels.

History Storage entries receive a dedicated semantic mapping:

| Event | Visual concept | Supporting label |
|---|---|---|
| Check-in | Item entering Storage with a plus | Check in |
| Edit | Pencil on a small record | Edited |
| Move | Item moving between two locations | Moved |
| Manual consumption | Bite/utensil or item leaving Storage | Used |
| Cooking | Simple cooking pot | Cooked |
| Discard | Waste bin | Discarded |
| Reversal | One clear curved return arrow | Reversed |

The event label remains adjacent to the icon, so color and icon shape are supplementary. Event surfaces may use restrained semantic tints to improve scanning, but their meaning must remain clear in monochrome.

History food identity must pass the recorded `foodKey` to `FoodToken`. Curated foods therefore render their established colored Food Token instead of an unrelated monogram or fallback. Cooking events continue to show the compact composition of affected Food Tokens.

Audit the existing Storage detail, Recipe Editor, History, and primary navigation icon usages for duplicate or ambiguous meanings. Correct clear problems within the shared icon registry; do not introduce a second icon library, emoji, or decorative icons.

## Components and Data Flow

- `FridgePalLoader.vue` owns loader markup, variants, accessible status behavior, and character animation hooks.
- The current brand asset remains the canonical static mark for headers. The loader reuses its geometry in layered inline SVG so body parts can move together without modifying every static brand use.
- App-level initialization derives its loader state from inventory hydration rather than a fixed timer.
- Recipe discovery derives its compact loader state from the existing Rescue search state.
- `AppIcon.vue` remains the icon registry. History maps event types to clearer icon names and passes `foodKey` through to `FoodToken`.

No loading or icon change modifies inventory, History, Rescue, or recipe data contracts.

## Error and State Behavior

- A failed initial load replaces the loader with the existing explicit disconnected/error state.
- A failed recipe search removes the loader while preserving the selected-food rail and Retry path.
- A loader never remains visible after its associated promise settles.
- Repeated route changes must not create overlapping full-page loaders.

## Verification

- Add component tests for page and compact loader variants, localized status text, and reduced-motion behavior.
- Add tests for the History event-to-icon mapping and curated `foodKey` forwarding.
- Verify the loop visually at a representative mobile viewport and desktop viewport.
- Verify English and Simplified Chinese loading copy, keyboard navigation, status announcement, and 200% zoom.
- Run frontend lint, type checking, build, relevant component tests, and the affected Playwright flows.

## Requirement Traceability

- `UI-CMP-01` Food Token consistency
- `UI-CMP-07` Functional iconography
- `UI-11` History event clarity
- `NFR-A11Y-002` Non-color status communication
- `NFR-A11Y-003` Reduced motion and zoom
- `NFR-PERF-003` Storage usable-content target
