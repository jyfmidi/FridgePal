# Multi-User Login Design

**Status:** Approved on 2026-07-21
**Requirements:** Reopens `OQ-03`; supersedes the no-auth invariant in `AGENTS.md`, `FR-DEP-002`, and the Non-Goals entry "Accounts, shared households, and permissions".

## Problem

Fridge Pal is currently a no-auth private-network application. To support a public hackathon demo on a single server, each visitor (judge, evaluator, guest) must be able to log in and see only their own data. The single-household data model has no ownership dimension, so every user would see and mutate the same inventory.

## Product Direction Change

This slice reopens `OQ-03` and changes the deployment exposure decision from "private LAN/loopback, no authentication" to "protected external exposure with application-level authentication and per-user data isolation." All canonical documents that hard-code the no-auth assumption must be updated in the same slice.

## Decisions

- **Account model:** open registration; each newly registered user receives an independent copy of the demo inventory.
- **Login mechanism:** username plus password, bcrypt-hashed server-side.
- **Session:** JWT in an `HttpOnly` + `SameSite=Strict` cookie.
- **Isolation enforcement:** Approach A — every repository method receives `user_id` as an explicit parameter and every query carries `WHERE user_id = :user_id`.
- **Demo data:** migration clears all existing user-owned rows; startup creates one built-in `demo` account with demo data; registration clones an independent demo copy into the new user's scope.

## Architecture and Data Model

### New `users` table

| Column | Type | Constraints |
|---|---|---|
| `id` | String(36) | Primary key |
| `username` | String(32) | Unique, not null |
| `password_hash` | String(255) | Not null (bcrypt) |
| `is_demo` | Boolean | Default false |
| `created_at` | DateTime(timezone=True) | Default utc_now |

### User-owned tables gain `user_id`

The following tables gain a non-null `user_id` foreign key to `users.id`, indexed:

- `inventory_lots`
- `inventory_transactions`
- `activity_events`
- `rescue_sessions`
- `saved_recipes`

`food_definitions` is shared reference data and does **not** gain `user_id`.

### Isolation mechanism

Repository method signatures gain a `user_id: str` parameter. Every SELECT, UPDATE, and DELETE against a user-owned table includes `WHERE user_id = :user_id`. The API layer resolves the current user via a `current_user` dependency and passes `user.id` down through the service layer into repositories.

### New backend module structure

```
backend/app/
  auth/                        # new
    __init__.py
    password.py                # bcrypt hash/verify
    jwt.py                     # JWT encode/decode (HS256)
    dependencies.py            # current_user dependency
    service.py                 # register, login, logout use cases
  api/
    auth.py                    # new: /api/auth/{register,login,logout,me}
    inventory.py  rescue.py  recipes.py  history.py   # modified: add current_user dependency
  infrastructure/db/
    models.py                  # modified: add UserRow + user_id on five tables
    demo_seed.py               # modified: accept user_id, seed per-user
```

### Migration strategy (Alembic)

1. Create the `users` table.
2. Add a nullable `user_id` column to the five user-owned tables.
3. Delete all existing rows from the five user-owned tables (per the "clear existing data on migration" decision).
4. Alter `user_id` to NOT NULL on the five tables.
5. Create the built-in `demo` account using `FRIDGE_PAL_DEMO_PASSWORD`.
6. At application startup, `seed_demo_inventory(factory, user_id=demo_user.id)` populates the demo account only.

### New environment variables

| Variable | Purpose |
|---|---|
| `FRIDGE_PAL_JWT_SECRET` | JWT signing secret. Required; startup fails if missing or shorter than 32 characters. |
| `FRIDGE_PAL_DEMO_PASSWORD` | Password for the built-in `demo` account. Required. |
| `FRIDGE_PAL_COOKIE_SECURE` | Sets the `Secure` cookie flag. Default `false` for local dev, set `true` in production. |

## API and Authentication Flow

### New endpoints

| Method | Path | Behavior |
|---|---|---|
| POST | `/api/auth/register` | Body `{username, password}` → create user → clone demo data → set cookie → return user info |
| POST | `/api/auth/login` | Body `{username, password}` → verify → set cookie → return user info |
| POST | `/api/auth/logout` | Clear the session cookie |
| GET | `/api/auth/me` | Return current user info; 401 if unauthenticated |

### Cookie specification

```
Set-Cookie: fp_session=<JWT>; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400; Secure=<env>
```

- JWT payload: `{ "sub": user_id, "username": "...", "is_demo": bool, "exp": ... }`
- Expiry: 24 hours.

### `current_user` dependency

```
current_user = Depends(verify_jwt_from_cookie)
```

Reads `fp_session` cookie → decodes JWT → confirms user still exists in DB → returns `UserContext(user_id, username, is_demo)`. Returns 401 on missing, invalid, expired, or unknown-user tokens. Applied to inventory, rescue, recipes, and history routers. `health.py` stays public.

### Frontend flow

1. New `frontend/src/api/auth.ts` client: register, login, logout, me.
2. New `auth` feature store (matching existing frontend patterns): holds `currentUser`, exposes `isAuthenticated`.
3. `router.ts` gains a global beforeEach guard: unauthenticated access to any route except `/login` and `/register` redirects to `/login`.
4. New `Login.vue` and `Register.vue` views.
5. `App.vue` gains a top-bar user widget: username + logout button.
6. Existing API clients (`inventory.ts`, `rescue.ts`, `recipes.ts`, `history.ts`) add `credentials: 'include'` so the cookie is sent automatically.

### Routers requiring `current_user`

Each `build_xxx_router(get_session)` becomes `build_xxx_router(get_session, current_user)`. Each endpoint signature gains `user: UserContext = Depends(current_user)` and passes `user.id` into service and repository calls:

- `inventory.py`
- `rescue.py`
- `recipes.py`
- `history.py`

## Security, Error Handling, and Testing

### Security boundary

1. Passwords are bcrypt-hashed (cost 12); `password_hash` is never returned in any response.
2. Username rules: 3-32 characters, `^[a-zA-Z0-9_-]+$`, case-sensitive, unique.
3. Password policy: minimum 8 characters; no complexity rules for the hackathon demo.
4. No rate limiting or CAPTCHA on registration — acceptable for the demo, must be added before any production use beyond the hackathon.
5. `FRIDGE_PAL_JWT_SECRET` is validated at startup; missing or shorter than 32 characters fails startup.
6. Existing inventory invariants (transactional, idempotent, non-negative, auditable, reversible) are preserved — transactions simply gain a `user_id` dimension.
7. Cross-user access to another user's resource (e.g. a lot_id owned by someone else) returns 404, never 403, to avoid leaking existence.

### Error responses

| Scenario | Status | Body |
|---|---|---|
| Unauthenticated access to protected endpoint | 401 | `{detail: "Not authenticated"}` |
| JWT invalid or expired | 401 | `{detail: "Invalid session"}` |
| Username already exists | 409 | `{detail: "Username already exists"}` |
| Username or password format invalid | 422 | FastAPI validation default |
| Login credentials incorrect | 401 | `{detail: "Invalid credentials"}` |
| Accessing another user's resource | 404 | `{detail: "Not found"}` |

### Testing strategy

**Backend (pytest, extending `backend/tests/`):**

- `auth/test_password.py` — bcrypt hash and verify.
- `auth/test_jwt.py` — encode, decode, expiry, tamper detection.
- `auth/test_service.py` — register (success, username conflict, format validation), login (success, wrong password, unknown user), logout.
- `api/test_auth_endpoints.py` — full status code coverage for the four endpoints.
- `api/test_isolation.py` — core: user A creates a lot, user B cannot see it; user B operating on A's lot_id returns 404.
- Existing `test_inventory.py` and peers are refactored to create a user and attach the cookie.

**Frontend:** no new component tests; existing lint, typecheck, and build must pass.

**E2E (optional):** register → see demo data → logout → login as `demo` → see different data.

## Documentation Updates

| Document | Change |
|---|---|
| `AGENTS.md` | Non-Negotiable Invariants: update the no-auth line; update OQ-03 reference in Decision Gates. |
| `docs/PRODUCT_REQUIREMENTS.md` | OQ-03: change to "protected external exposure with auth"; rewrite or remove `FR-DEP-002`; remove "Accounts, shared households, and permissions" from Non-Goals. |
| `docs/IMPLEMENTATION_PLAN.md` | Tech Stack paragraph: update auth status; add this slice. |
| `docs/DEPLOYMENT.md` | Public deployment requirements: JWT secret and demo password are mandatory; cookie secure flag guidance. |
| `README.md` | Security boundary paragraph rewrite; environment variable table adds the three new variables. |
| `docs/DOMAIN_AND_AI_CONTRACTS.md` | Add the per-user isolation invariant. |

## Verification

- Backend: `pytest -q`, `ruff check app tests`, `mypy app` all clean.
- Frontend: `npm run lint`, `npm run typecheck`, `npm run build` all clean.
- `api/test_isolation.py` passes: cross-user access returns 404, no data leaks.
- Fresh migration from a clean database produces the `demo` account with demo data.
- Registration of a new user clones demo data into that user's scope only.
- `docker compose config --quiet` validates the updated environment.
