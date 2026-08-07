# Personal Food Isolation Design

## Goal

Keep user-created foods private to their creator while preserving one shared, Admin-managed preset library. Two users may create foods with the same display name without sharing definitions, changing each other's base units, or exposing names through Add Food or Admin.

## Scope

This change adds personal ownership to the existing `FoodDefinition` model. It does not add submission, moderation, publishing, merge, or duplicate-resolution workflows. Admin continues to manage public presets only and cannot browse personal foods.

## Data model

Add nullable, indexed `owner_user_id` to `food_definitions`:

- `NULL` means a public definition. Seeded and Admin-created definitions are public.
- A user ID means a personal definition visible and reusable only by that user.
- `active` remains the soft-availability flag and is not reused as a visibility flag.
- `origin` continues to describe how the row was created; it does not grant visibility.

No new table is required. Inventory lots and activity events keep their existing `food_definition_id` foreign key, so Storage, History, Rescue, and recipe flows retain one canonical reference shape.

The owner index bounds the user-scoped library query. At household usage rates, FoodDefinition growth is small compared with lot, transaction, and history growth: hundreds of thousands of compact personal definitions remain ordinary relational-table scale.

## Personal identity and collision policy

The frontend may continue sending its temporary `custom:<slug>` key. The server derives the persisted personal food ID from a stable UUID namespace containing both `user_id` and that custom key. Therefore:

- repeated creation of the same normalized custom key by one user reuses one definition;
- the same name created by two users produces different IDs;
- a client cannot choose another user's personal ID for a new check-in;
- public food keys remain stable and unchanged.

The personal definition keeps the submitted localized names, base unit, recommended location, and deterministic monogram visual key. It has no public aliases, package presets, or shelf-life rules unless future personal-edit functionality explicitly adds them.

## Read and write authorization

`GET /api/library` returns active public definitions plus active personal definitions owned by the authenticated user. It never returns another user's definitions.

The frontend clears its module-level Food Library cache whenever authentication changes. An in-flight response from the previous session is generation-guarded and cannot repopulate the cache after logout or account switching.

Check-in accepts a definition only when it is active and either public or owned by the authenticated user. An inaccessible, inactive, or foreign personal ID returns 404-style not-found behavior rather than revealing that the definition exists.

Admin list, detail, update, icon, and delete operations operate only on public definitions. A guessed personal ID is treated as not found. Admin creation always writes `owner_user_id = NULL`.

Existing Storage and History reads remain user-scoped through their owning lots/events. They may still render an inactive definition referenced by historical data.

## Existing data

Existing rows receive `owner_user_id = NULL` during schema upgrade for backward compatibility. Existing `custom:*` rows cannot be assigned safely because the old schema did not record whether they came from Admin or a user and may already be shared by multiple users.

The deployment is still in active MVP development, so existing local custom definitions should be recreated under the new ownership rule when privacy matters. The migration does not guess ownership, rewrite historical foreign keys, or silently hide an existing shared definition. The new privacy guarantee applies to every custom definition created after the upgrade.

## Failure and transaction behavior

Personal definition creation remains inside the same check-in transaction as its InventoryLot and ActivityEvent. A failed check-in rolls back the definition as well. The existing idempotency key remains the mutation replay boundary.

Concurrent first check-ins of the same personal key rely on the deterministic ID and database uniqueness. A uniqueness race is handled as a normal idempotent/retryable conflict without creating duplicate personal definitions.

## Verification

- Two users creating the same custom name receive different food-definition IDs.
- Each user sees the public library plus only their personal definitions.
- A crafted check-in using another user's personal ID returns not found and creates no lot or event.
- Admin list and direct mutation endpoints do not expose personal definitions.
- Seeded and Admin-created presets remain public and shared.
- Repeated personal check-in reuses the same definition and converts compatible units against its base unit.
- Fresh SQLite schema, legacy-column upgrade, MySQL-compatible schema metadata, backend integration tests, frontend checks, and mobile/desktop Add Food coverage pass.
