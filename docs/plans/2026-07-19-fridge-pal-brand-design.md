# Fridge Pal Brand Rename and Logo Design

**Status:** Approved for implementation  
**Date:** 2026-07-19

## Goal

Rename the product from **Fridgital** to **Fridge Pal** and introduce a standalone app mark that feels like a small, friendly coding-agent character while remaining recognizable as a two-door refrigerator.

## Brand Mark

The mark is a compact, near-square refrigerator character built from simple geometric blocks:

- two vertically stacked coral-orange door blocks;
- a shorter upper door and taller lower door;
- two small white rectangular eyes on the upper door;
- a narrow door gap and minimal refrigerator detail;
- one short dark-coral handle/notch, deliberately distinct from the white eyes;
- restrained corner rounding that preserves a light pixel-character quality.

The mark contains no wordmark or other text. It uses no gradient, shadow, outline, blue system color, facial mouth, appliance scenery, or decorative effects.

## Color Relationship

The logo takes its identity from the product's warm expiration spectrum rather than the interface's blue interaction color. Coral orange is the dominant brand color. White is reserved for the character's eyes and negative space. A darker coral may be used for the handle or door detail so appliance controls cannot be confused with facial features.

## Product Integration

- The canonical product name becomes **Fridge Pal** in product, UX, technical, deployment, runtime, localization, and test surfaces.
- The standalone mark appears beside the product name only where the application already exposes a global brand identity. The SVG itself never contains text.
- Focused task headers continue to omit brand identity.
- The mark must remain legible at favicon and compact mobile-header sizes.
- The existing blue interaction system and warm inventory/urgency surfaces remain otherwise unchanged.

## Deliverables

- one deterministic, production-ready SVG mark in the frontend public brand assets;
- favicon integration using the same standalone mark;
- compact global-header integration with localized accessible naming;
- canonical documentation and runtime rename from Fridgital to Fridge Pal;
- updated tests covering the new title and visible header identity.

## Verification

- Inspect the mark at favicon, 24 px, and compact header sizes.
- Verify mobile and desktop headers retain their existing hierarchy.
- Verify the SVG contains no text and the handle cannot be read as an additional eye.
- Run frontend lint, typecheck, build, relevant backend tests, and the title/header smoke test.
- Search the repository for stale user-facing or canonical `Fridgital` references.
