# Multi-User Login Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add username/password authentication with per-user data isolation so Fridge Pal can be demoed publicly on a single server.

**Architecture:** JWT in httpOnly cookies for sessions. A new `users` table. Five user-owned tables gain a non-null `user_id` FK. Every repository query carries `WHERE user_id = :user_id` (Approach A: explicit parameter passing, no contextvar magic). Registration clones demo data into the new user's scope. A built-in `demo` account is created at startup.

**Tech Stack:** FastAPI, SQLAlchemy 2, bcrypt, PyJWT, Vue 3 + TypeScript, vue-router.

**Design doc:** `docs/plans/2026-07-21-multi-user-login-design.md`

**Worktree:** `/Users/jyfmidi/Dev/Frigital/.worktrees/multi-user-login` (branch `feature/multi-user-login`)

**Baseline:** 208 backend tests passing.

**Settings env vars (canonical names):** `FRIDGE_PAL_JWT_SECRET` (>= 32 chars, required), `FRIDGE_PAL_DEMO_PASSWORD` (required), `FRIDGE_PAL_COOKIE_SECURE` (default false).

---

## Task 1: Add bcrypt and PyJWT dependencies

**Files:** Modify `backend/pyproject.toml`

**Step 1:** Add to `dependencies` in `backend/pyproject.toml`:
```toml
    "bcrypt>=4.1",
    "pyjwt>=2.8",
```

**Step 2:** Run: `cd backend && .venv/bin/pip install -e '.[dev]'`
Expected: successful install.

**Step 3:** Run: `cd backend && .venv/bin/python -c "import bcrypt, jwt; print('ok')"`
Expected: `ok`

**Step 4:** Commit:
```bash
git add backend/pyproject.toml
git commit -m "feat: add bcrypt and pyjwt dependencies for auth"
```

---

## Task 2: Add UserRow model and user_id FK on five user-owned tables

**Files:** Modify `backend/app/infrastructure/db/models.py`

**Step 1:** Add `UserRow` class before `FoodDefinitionRow`:
```python
class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

**Step 2:** Add this line to `InventoryLotRow`, `InventoryTransactionRow`, `ActivityEventRow`, `RescueSessionRow`, `SavedRecipeRow` (each gets a non-null indexed FK):
```python
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
```

**Step 3:** Run: `cd backend && .venv/bin/pytest -q`
Expected: Many failures (existing tests don't supply `user_id`). This is expected; fixed in later tasks. Note the count.

**Step 4:** Commit:
```bash
git add backend/app/infrastructure/db/models.py
git commit -m "feat: add UserRow and user_id FK on five user-owned tables"
```

---

## Task 3: Add auth settings to config.py

**Files:** Modify `backend/app/config.py`, Create `backend/tests/conftest.py`

**Step 1:** In `backend/app/config.py`, add `Field` import from pydantic, then add to `Settings`:
```python
    jwt_secret: str = Field(default="", alias="FRIDGE_PAL_JWT_SECRET")
    demo_password: str = Field(default="", alias="FRIDGE_PAL_DEMO_PASSWORD")
    cookie_secure: bool = Field(default=False, alias="FRIDGE_PAL_COOKIE_SECURE")
```

**Step 2:** Create `backend/tests/conftest.py`:
```python
import os

os.environ.setdefault("FRIDGE_PAL_JWT_SECRET", "test-secret-at-least-thirty-two-characters-long!!")
os.environ.setdefault("FRIDGE_PAL_DEMO_PASSWORD", "demo-pass-123")
```

**Step 3:** Run: `cd backend && .venv/bin/python -c "from app.config import get_settings; print(get_settings().jwt_secret)"`
Expected: prints the test secret from conftest (may need `cd backend && FRIDGE_PAL_JWT_SECRET=test python -c ...` if conftest not auto-loaded).

**Step 4:** Commit:
```bash
git add backend/app/config.py backend/tests/conftest.py
git commit -m "feat: add JWT secret, demo password, cookie secure settings"
```

---

## Task 4: Write auth/password.py (bcrypt hash and verify)

**Files:** Create `backend/app/auth/__init__.py` (empty), `backend/app/auth/password.py`, `backend/tests/unit/auth/__init__.py` (empty), `backend/tests/unit/auth/test_password.py`

**Step 1 — failing test** in `backend/tests/unit/auth/test_password.py`:
```python
from app.auth.password import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_hash_is_unique_per_call():
    assert hash_password("secret123") != hash_password("secret123")
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_password.py -v`
Expected: FAIL (ModuleNotFoundError).

**Step 3 — implementation** in `backend/app/auth/password.py`:
```python
"""bcrypt password hashing and verification."""

import bcrypt


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_password.py -v`
Expected: 3 passed.

**Step 5:** Commit:
```bash
git add backend/app/auth/__init__.py backend/app/auth/password.py backend/tests/unit/auth/
git commit -m "feat: add bcrypt password hashing module"
```

---

## Task 5: Write auth/jwt.py (JWT encode/decode)

**Files:** Create `backend/app/auth/jwt.py`, `backend/tests/unit/auth/test_jwt.py`

**Step 1 — failing test** in `backend/tests/unit/auth/test_jwt.py`:
```python
from datetime import timedelta

import pytest

from app.auth.jwt import TokenError, decode_token, encode_token


def test_encode_decode_roundtrip():
    token = encode_token("user-123", "alice", is_demo=False)
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["username"] == "alice"
    assert payload["is_demo"] is False


def test_decode_invalid_token_raises():
    with pytest.raises(TokenError):
        decode_token("not-a-jwt")


def test_decode_expired_token_raises():
    token = encode_token("user-123", "alice", is_demo=False, expires_in=timedelta(seconds=-1))
    with pytest.raises(TokenError):
        decode_token(token)
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_jwt.py -v`
Expected: FAIL (ModuleNotFoundError).

**Step 3 — implementation** in `backend/app/auth/jwt.py`:
```python
"""JWT encode/decode using HS256. Secret comes from Settings."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config import get_settings


class TokenError(Exception):
    """Raised when a JWT cannot be decoded or is invalid."""


def encode_token(
    user_id: str,
    username: str,
    *,
    is_demo: bool,
    expires_in: timedelta | None = None,
) -> str:
    settings = get_settings()
    if expires_in is None:
        expires_in = timedelta(hours=24)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "is_demo": is_demo,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise TokenError(str(error)) from error
```

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_jwt.py -v`
Expected: 3 passed (test conftest from Task 3 sets the secret).

**Step 5:** Commit:
```bash
git add backend/app/auth/jwt.py backend/tests/unit/auth/test_jwt.py
git commit -m "feat: add JWT encode/decode module"
```

---

## Task 6: Write auth/service.py (register, login, get_user)

**Files:** Create `backend/app/auth/service.py`, `backend/tests/unit/auth/test_service.py`

**Step 1 — failing test** in `backend/tests/unit/auth/test_service.py`:
```python
import pytest
from sqlalchemy.orm import Session

from app.auth.service import (
    LoginError,
    RegisterError,
    UserContext,
    authenticate_user,
    create_user,
    get_user_by_id,
)
from app.infrastructure.db.session import create_database


@pytest.fixture()
def session():
    _, factory = create_database("sqlite:///:memory:")
    with factory() as s:
        yield s


def test_create_user_and_authenticate(session: Session):
    user = create_user(session, "alice", "password123")
    assert user.username == "alice"
    assert user.is_demo is False
    ctx = authenticate_user(session, "alice", "password123")
    assert ctx.user_id == user.id


def test_authenticate_wrong_password(session: Session):
    create_user(session, "alice", "password123")
    with pytest.raises(LoginError):
        authenticate_user(session, "alice", "wrong")


def test_authenticate_unknown_user(session: Session):
    with pytest.raises(LoginError):
        authenticate_user(session, "ghost", "password123")


def test_create_user_duplicate_username(session: Session):
    create_user(session, "alice", "password123")
    with pytest.raises(RegisterError):
        create_user(session, "alice", "different456")


def test_create_user_invalid_username(session: Session):
    with pytest.raises(RegisterError):
        create_user(session, "ab", "password123")
    with pytest.raises(RegisterError):
        create_user(session, "bad name!", "password123")


def test_create_user_short_password(session: Session):
    with pytest.raises(RegisterError):
        create_user(session, "alice", "short")


def test_get_user_by_id(session: Session):
    user = create_user(session, "alice", "password123")
    fetched = get_user_by_id(session, user.id)
    assert fetched is not None
    assert fetched.username == "alice"


def test_get_user_by_id_not_found(session: Session):
    assert get_user_by_id(session, "nonexistent") is None
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_service.py -v`
Expected: FAIL (ModuleNotFoundError).

**Step 3 — implementation** in `backend/app/auth/service.py`:
```python
"""User registration and authentication use cases."""

import re
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.password import hash_password, verify_password
from app.infrastructure.db.models import UserRow

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
USERNAME_MIN_LEN = 3
USERNAME_MAX_LEN = 32
PASSWORD_MIN_LEN = 8


class RegisterError(Exception):
    """Raised when registration fails validation or uniqueness."""


class LoginError(Exception):
    """Raised when login credentials are invalid."""


@dataclass(frozen=True)
class UserContext:
    user_id: str
    username: str
    is_demo: bool


def create_user(
    session: Session,
    username: str,
    password: str,
    *,
    is_demo: bool = False,
) -> UserRow:
    if len(username) < USERNAME_MIN_LEN or len(username) > USERNAME_MAX_LEN:
        raise RegisterError(f"Username must be {USERNAME_MIN_LEN}-{USERNAME_MAX_LEN} characters.")
    if not USERNAME_PATTERN.match(username):
        raise RegisterError("Username may only contain letters, numbers, underscores, and hyphens.")
    if len(password) < PASSWORD_MIN_LEN:
        raise RegisterError(f"Password must be at least {PASSWORD_MIN_LEN} characters.")

    existing = session.scalar(select(UserRow).where(UserRow.username == username))
    if existing is not None:
        raise RegisterError("Username already exists.")

    user = UserRow(
        id=str(uuid4()),
        username=username,
        password_hash=hash_password(password),
        is_demo=is_demo,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, username: str, password: str) -> UserContext:
    user = session.scalar(select(UserRow).where(UserRow.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise LoginError("Invalid credentials.")
    return UserContext(user_id=user.id, username=user.username, is_demo=user.is_demo)


def get_user_by_id(session: Session, user_id: str) -> UserRow | None:
    return session.get(UserRow, user_id)
```

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_service.py -v`
Expected: 8 passed.

**Step 5:** Commit:
```bash
git add backend/app/auth/service.py backend/tests/unit/auth/test_service.py
git commit -m "feat: add user registration and authentication service"
```

---

## Task 7: Write auth/dependencies.py (current_user FastAPI dependency)

**Files:** Create `backend/app/auth/dependencies.py`, `backend/tests/unit/auth/test_dependencies.py`

**Step 1 — failing test** in `backend/tests/unit/auth/test_dependencies.py`:
```python
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.auth.dependencies import current_user_factory
from app.auth.jwt import encode_token
from app.auth.service import create_user
from app.infrastructure.db.session import create_database


@pytest.fixture()
def deps():
    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        user = create_user(session, "alice", "password123")
        yield session, user, current_user_factory(factory)


def test_current_user_valid_cookie(deps):
    _, user, current_user = deps
    token = encode_token(user.id, user.username, is_demo=False)
    request = Request(scope={"type": "http", "headers": [(b"cookie", f"fp_session={token}".encode())]})
    ctx = current_user(request)
    assert ctx.user_id == user.id


def test_current_user_missing_cookie(deps):
    _, _, current_user = deps
    request = Request(scope={"type": "http", "headers": []})
    with pytest.raises(HTTPException) as exc:
        current_user(request)
    assert exc.value.status_code == 401


def test_current_user_invalid_token(deps):
    _, _, current_user = deps
    request = Request(scope={"type": "http", "headers": [(b"cookie", b"fp_session=not-a-jwt")]})
    with pytest.raises(HTTPException) as exc:
        current_user(request)
    assert exc.value.status_code == 401


def test_current_user_unknown_user(deps):
    _, _, current_user = deps
    token = encode_token("nonexistent", "ghost", is_demo=False)
    request = Request(scope={"type": "http", "headers": [(b"cookie", f"fp_session={token}".encode())]})
    with pytest.raises(HTTPException) as exc:
        current_user(request)
    assert exc.value.status_code == 401
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_dependencies.py -v`
Expected: FAIL (ModuleNotFoundError).

**Step 3 — implementation** in `backend/app/auth/dependencies.py`:
```python
"""FastAPI dependency that resolves the current authenticated user from a JWT cookie."""

from collections.abc import Callable
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from app.auth.jwt import TokenError, decode_token
from app.auth.service import UserContext, get_user_by_id
from app.config import get_settings

COOKIE_NAME = "fp_session"


@lru_cache
def _cookie_secure() -> bool:
    return get_settings().cookie_secure


def current_user_factory(
    session_factory: sessionmaker[Session],
) -> Callable[[Request], UserContext]:
    def current_user(request: Request) -> UserContext:
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = decode_token(token)
        except TokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        with session_factory() as session:
            user = get_user_by_id(session, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        return UserContext(user_id=user.id, username=user.username, is_demo=user.is_demo)

    return current_user


def set_session_cookie(response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        max_age=86400,
        path="/",
        secure=_cookie_secure(),
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")
```

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/unit/auth/test_dependencies.py -v`
Expected: 4 passed.

**Step 5:** Commit:
```bash
git add backend/app/auth/dependencies.py backend/tests/unit/auth/test_dependencies.py
git commit -m "feat: add current_user FastAPI dependency"
```

---

## Task 8: Update demo_seed.py to seed per-user

**Files:** Modify `backend/app/infrastructure/db/demo_seed.py`, `backend/tests/integration/test_demo_seed.py`

**Step 1:** Rename `seed_demo_inventory` to `seed_demo_inventory_for_user(factory, user_id, today=None)` in `backend/app/infrastructure/db/demo_seed.py`. Key changes inside:
- `idempotency_key` becomes `f"demo-seed-{user_id}-{food_key}"`
- `InventoryLotRow.id` becomes `f"demo-lot-{user_id}-{food_key}"`
- `ActivityEventRow.id` becomes `f"demo-event-{user_id}-{food_key}"`
- Each `InventoryLotRow(...)` and `ActivityEventRow(...)` gets `user_id=user_id`
- Keep `FoodDefinitionRow` unchanged (shared reference data — no `user_id`)

**Step 2:** Add a test in `backend/tests/integration/test_demo_seed.py`:
```python
from app.auth.service import create_user
from app.infrastructure.db.demo_seed import seed_demo_inventory_for_user
from app.infrastructure.db.models import InventoryLotRow
from app.infrastructure.db.session import create_database
from sqlalchemy import select


def test_seed_for_user_creates_user_scoped_lots():
    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        user = create_user(session, "alice", "password123")
    seed_demo_inventory_for_user(factory, user.id)
    with factory() as session:
        lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == user.id)
        ).all()
        assert len(lots) == 16  # DEMO_FOODS count
        for lot in lots:
            assert lot.user_id == user.id


def test_seed_for_two_users_does_not_collide():
    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        u1 = create_user(session, "alice", "password123")
        u2 = create_user(session, "bob", "password456")
    seed_demo_inventory_for_user(factory, u1.id)
    seed_demo_inventory_for_user(factory, u2.id)
    with factory() as session:
        u1_lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == u1.id)
        ).all()
        u2_lots = session.scalars(
            select(InventoryLotRow).where(InventoryLotRow.user_id == u2.id)
        ).all()
        assert len(u1_lots) == 16
        assert len(u2_lots) == 16
```

**Step 3:** Run: `cd backend && .venv/bin/pytest tests/integration/test_demo_seed.py -v`
Expected: new tests pass; existing demo seed tests may need updating to call `seed_demo_inventory_for_user` with a user_id (fix them here).

**Step 4:** Commit:
```bash
git add backend/app/infrastructure/db/demo_seed.py backend/tests/integration/test_demo_seed.py
git commit -m "feat: parameterize demo seed by user_id"
```

---

## Task 9: Write api/auth.py (register, login, logout, me endpoints)

**Files:** Create `backend/app/api/auth.py`, `backend/tests/integration/test_auth_api.py`

**Step 1 — failing test** in `backend/tests/integration/test_auth_api.py`:
```python
from fastapi.testclient import TestClient

from app.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_register_sets_cookie_and_returns_user():
    r = _client().post("/api/auth/register", json={"username": "alice", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "alice"
    assert "password" not in str(body)
    assert "fp_session" in r.cookies


def test_register_duplicate_returns_409():
    c = _client()
    c.post("/api/auth/register", json={"username": "alice", "password": "password123"})
    r = c.post("/api/auth/register", json={"username": "alice", "password": "different456"})
    assert r.status_code == 409


def test_register_invalid_username_returns_422():
    r = _client().post("/api/auth/register", json={"username": "ab", "password": "password123"})
    assert r.status_code == 422


def test_login_sets_cookie():
    c = _client()
    c.post("/api/auth/register", json={"username": "bob", "password": "password123"})
    c.cookies.clear()
    r = c.post("/api/auth/login", json={"username": "bob", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["username"] == "bob"
    assert "fp_session" in r.cookies


def test_login_wrong_password_returns_401():
    c = _client()
    c.post("/api/auth/register", json={"username": "bob", "password": "password123"})
    c.cookies.clear()
    r = c.post("/api/auth/login", json={"username": "bob", "password": "wrong"})
    assert r.status_code == 401


def test_logout_clears_cookie():
    c = _client()
    c.post("/api/auth/register", json={"username": "carol", "password": "password123"})
    r = c.post("/api/auth/logout")
    assert r.status_code == 200


def test_me_returns_current_user():
    c = _client()
    c.post("/api/auth/register", json={"username": "dave", "password": "password123"})
    r = c.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["username"] == "dave"


def test_me_without_auth_returns_401():
    r = _client().get("/api/auth/me")
    assert r.status_code == 401


def test_register_clones_demo_data():
    c = _client()
    c.post("/api/auth/register", json={"username": "eve", "password": "password123"})
    r = c.get("/api/storage")
    assert r.status_code == 200
    assert len(r.json()["inventory"]) > 0
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/integration/test_auth_api.py -v`
Expected: FAIL (endpoints don't exist yet).

**Step 3 — implementation** in `backend/app/api/auth.py`:
```python
"""HTTP boundary for authentication endpoints."""

import re
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import (
    clear_session_cookie,
    current_user_factory,
    set_session_cookie,
)
from app.auth.jwt import encode_token
from app.auth.service import (
    LoginError,
    RegisterError,
    UserContext,
    authenticate_user,
    create_user,
)
from app.infrastructure.db.demo_seed import seed_demo_inventory_for_user

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_pattern(cls, value: str) -> str:
        if not USERNAME_PATTERN.match(value):
            raise ValueError("Username may only contain letters, numbers, underscores, and hyphens.")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    username: str
    is_demo: bool


def build_auth_router(
    session_provider: Callable[[], Session],
    session_factory: sessionmaker[Session],
    current_user: Callable[..., UserContext],
) -> APIRouter:
    api = APIRouter()

    @api.post("/auth/register", status_code=status.HTTP_201_CREATED)
    def register(payload: RegisterRequest, response: Response) -> UserResponse:
        session = next(session_provider())
        try:
            user = create_user(session, payload.username, payload.password)
        except RegisterError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        seed_demo_inventory_for_user(session_factory, user.id)
        token = encode_token(user.id, user.username, is_demo=user.is_demo)
        set_session_cookie(response, token)
        return UserResponse(username=user.username, is_demo=user.is_demo)

    @api.post("/auth/login")
    def login(payload: LoginRequest, response: Response) -> UserResponse:
        session = next(session_provider())
        try:
            ctx = authenticate_user(session, payload.username, payload.password)
        except LoginError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            ) from error
        token = encode_token(ctx.user_id, ctx.username, is_demo=ctx.is_demo)
        set_session_cookie(response, token)
        return UserResponse(username=ctx.username, is_demo=ctx.is_demo)

    @api.post("/auth/logout")
    def logout(response: Response) -> dict[str, str]:
        clear_session_cookie(response)
        return {"status": "ok"}

    @api.get("/auth/me")
    def me(user: Annotated[UserContext, Depends(current_user)]) -> UserResponse:
        return UserResponse(username=user.username, is_demo=user.is_demo)

    return api
```

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/integration/test_auth_api.py -v`
Expected: Most pass. `test_register_clones_demo_data` may fail until Task 11 wires `user_id` into inventory reads.

**Step 5:** Commit:
```bash
git add backend/app/api/auth.py backend/tests/integration/test_auth_api.py
git commit -m "feat: add auth API endpoints (register, login, logout, me)"
```

---

## Task 10: Wire auth router + demo account bootstrap into main.py

**Files:** Modify `backend/app/main.py`, Modify `backend/app/infrastructure/db/session.py`

**Step 1:** In `backend/app/infrastructure/db/session.py`, extend `_ensure_columns` to add nullable `user_id` to the 5 user-owned tables if missing. Since `Base.metadata.create_all` creates new tables (including `users`) automatically but won't add columns to existing tables, the `_ensure_columns` function must ALTER each table to add `user_id` when upgrading an existing database. For a fresh SQLite test database, `create_all` handles everything.

**Step 2:** In `backend/app/main.py`:
- Import `build_auth_router`, `current_user_factory`, `create_user`, `seed_demo_inventory_for_user`, `UserContext`.
- After `create_database`, build `current_user = current_user_factory(session_factory)`.
- Create the built-in `demo` account at startup: if no user with `username="demo"` exists, `create_user(session, "demo", settings.demo_password, is_demo=True)` then `seed_demo_inventory_for_user(session_factory, demo_user.id)`.
- Include the auth router: `app.include_router(build_auth_router(get_session, session_factory, current_user), prefix="/api")`.
- Update existing `build_xxx_router(get_session)` calls to also pass `current_user` (this is wired in Tasks 12-15 as each router is refactored; for now pass `current_user` only to the auth router).

**Step 3:** Run: `cd backend && .venv/bin/pytest tests/integration/test_auth_api.py -v`
Expected: All auth endpoint tests pass except `test_register_clones_demo_data` (inventory not yet user-scoped).

**Step 4:** Run: `cd backend && .venv/bin/pytest -q`
Expected: Pre-existing tests still fail (they don't supply `user_id`) — this is expected until Tasks 12-15.

**Step 5:** Commit:
```bash
git add backend/app/main.py backend/app/infrastructure/db/session.py
git commit -m "feat: wire auth router and demo account bootstrap at startup"
```

---

## Task 11: Refactor inventory service to accept user_id

**Files:** Modify `backend/app/application/inventory/service.py`

**Step 1:** Every public function in this module gains `user_id: str` as the second parameter (after `session`). The functions to update: `check_in_food`, `get_storage_overview`, `list_lots`, `edit_lot`, `reduce_inventory`, `discard_lot`, `cooking_preview`, `cooking_commit`.

**Step 2:** Every `InventoryLotRow(...)`, `InventoryTransactionRow(...)`, `ActivityEventRow(...)` constructor call gains `user_id=user_id`.

**Step 3:** Every `select(InventoryLotRow)` / `select(InventoryTransactionRow)` / `select(ActivityEventRow)` query gains `.where(X.user_id == user_id)`. Lookups by `lot_id` must also filter by `user_id` so user B operating on user A's lot_id returns 404 (not data leak).

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/integration/test_inventory_api.py -v`
Expected: FAIL (API layer doesn't pass `user_id` yet — wired in Task 12).

**Step 5:** Commit:
```bash
git add backend/app/application/inventory/service.py
git commit -m "feat: scope inventory service by user_id"
```

---

## Task 12: Wire current_user into inventory router

**Files:** Modify `backend/app/api/inventory.py`, Modify `backend/tests/integration/test_inventory_api.py`

**Step 1:** Change `build_inventory_router(session_provider)` to `build_inventory_router(session_provider, current_user)`. Each endpoint signature gains `user: Annotated[UserContext, Depends(current_user)]`. Each service call passes `user.id` as `user_id`.

**Step 2:** Update existing tests in `test_inventory_api.py` to register a user first and include the cookie. Add a helper fixture:
```python
@pytest.fixture()
def authed_client():
    client = TestClient(create_app())
    client.post("/api/auth/register", json={"username": "tester", "password": "password123"})
    return client
```
Replace all `client = TestClient(create_app())` with `client = authed_client` (or equivalent). Tests that asserted specific demo data counts must now account for the demo data cloned at registration.

**Step 3:** Run: `cd backend && .venv/bin/pytest tests/integration/test_inventory_api.py -v`
Expected: All pass.

**Step 4:** Commit:
```bash
git add backend/app/api/inventory.py backend/tests/integration/test_inventory_api.py
git commit -m "feat: wire current_user into inventory router"
```

---

## Task 13: Refactor rescue service + router to accept user_id

**Files:** Modify `backend/app/application/rescue/service.py`, `backend/app/api/rescue.py`, `backend/tests/integration/test_rescue_api.py`

**Step 1:** Add `user_id: str` to every public function in `rescue/service.py`. Every `RescueSessionRow(...)` constructor gains `user_id=user_id`. Every `select(RescueSessionRow)` gains `.where(RescueSessionRow.user_id == user_id)`.

**Step 2:** Change `build_rescue_router(session_provider, recipe_adapters)` to `build_rescue_router(session_provider, recipe_adapters, current_user)`. Each endpoint gains `user: Annotated[UserContext, Depends(current_user)]` and passes `user.id`.

**Step 3:** Update `test_rescue_api.py` with the same `authed_client` fixture pattern from Task 12.

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/integration/test_rescue_api.py -v`
Expected: All pass.

**Step 5:** Commit:
```bash
git add backend/app/application/rescue/service.py backend/app/api/rescue.py backend/tests/integration/test_rescue_api.py
git commit -m "feat: scope rescue service and router by user_id"
```

---

## Task 14: Refactor recipes service + router to accept user_id

**Files:** Modify `backend/app/application/recipes/service.py`, `backend/app/api/recipes.py`, `backend/tests/integration/test_recipes_api.py`

**Step 1:** Add `user_id: str` to every public function in `recipes/service.py`. Every `SavedRecipeRow(...)` gains `user_id=user_id`. Every `select(SavedRecipeRow)` gains `.where(SavedRecipeRow.user_id == user_id)`.

**Step 2:** Change `build_recipe_router(session_provider)` to `build_recipe_router(session_provider, current_user)`. Each endpoint gains `user: Annotated[UserContext, Depends(current_user)]` and passes `user.id`.

**Step 3:** Update `test_recipes_api.py` with the `authed_client` fixture pattern.

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/integration/test_recipes_api.py -v`
Expected: All pass.

**Step 5:** Commit:
```bash
git add backend/app/application/recipes/service.py backend/app/api/recipes.py backend/tests/integration/test_recipes_api.py
git commit -m "feat: scope recipes service and router by user_id"
```

---

## Task 15: Refactor history service + router to accept user_id

**Files:** Modify `backend/app/application/history/service.py`, `backend/app/api/history.py`, `backend/tests/integration/test_history_api.py`

**Step 1:** Add `user_id: str` to every public function in `history/service.py`. Every `select(ActivityEventRow)` / `select(InventoryTransactionRow)` gains `.where(X.user_id == user_id)`.

**Step 2:** Change `build_history_router(session_provider)` to `build_history_router(session_provider, current_user)`. Each endpoint gains `user: Annotated[UserContext, Depends(current_user)]` and passes `user.id`.

**Step 3:** Update `test_history_api.py` with the `authed_client` fixture pattern.

**Step 4:** Run: `cd backend && .venv/bin/pytest tests/integration/test_history_api.py -v`
Expected: All pass.

**Step 5:** Commit:
```bash
git add backend/app/application/history/service.py backend/app/api/history.py backend/tests/integration/test_history_api.py
git commit -m "feat: scope history service and router by user_id"
```

---

## Task 16: Write cross-user isolation integration test

**Files:** Create `backend/tests/integration/test_isolation.py`

**Step 1 — test** in `backend/tests/integration/test_isolation.py`:
```python
from fastapi.testclient import TestClient

from app.main import create_app


def _register_and_get_client(username: str) -> TestClient:
    client = TestClient(create_app())
    client.post("/api/auth/register", json={"username": username, "password": "password123"})
    return client


def test_user_cannot_see_other_users_storage():
    alice = _register_and_get_client("alice_iso")
    bob = _register_and_get_client("bob_iso")
    # Both have demo data; each should see only their own.
    alice_storage = alice.get("/api/storage").json()
    bob_storage = bob.get("/api/storage").json()
    # Same food keys but different lot IDs (per-user demo clone).
    alice_lot_ids = {item.get("lotId") for item in alice_storage.get("inventory", [])}
    bob_lot_ids = {item.get("lotId") for item in bob_storage.get("inventory", [])}
    assert alice_lot_ids and bob_lot_ids
    assert alice_lot_ids.isdisjoint(bob_lot_ids)


def test_user_cannot_patch_other_users_lot():
    alice = _register_and_get_client("alice_patch")
    bob = _register_and_get_client("bob_patch")
    alice_lot_id = alice.get("/api/storage").json()["inventory"][0]["lotId"]
    # Bob tries to edit Alice's lot.
    r = bob.patch(
        f"/api/lots/{alice_lot_id}",
        json={"idempotencyKey": "bob-attack-1", "quantity": 999, "unit": "g"},
    )
    assert r.status_code == 404


def test_user_cannot_discard_other_users_lot():
    alice = _register_and_get_client("alice_discard")
    bob = _register_and_get_client("bob_discard")
    alice_lot_id = alice.get("/api/storage").json()["inventory"][0]["lotId"]
    r = bob.post(f"/api/lots/{alice_lot_id}/discard", json={"idempotencyKey": "bob-attack-2"})
    assert r.status_code == 404


def test_unauthenticated_access_returns_401():
    client = TestClient(create_app())
    assert client.get("/api/storage").status_code == 401
    assert client.get("/api/inventory/lots?foodKey=spinach&location=FRIDGE").status_code == 401
    assert client.get("/api/history").status_code == 401
```

**Step 2:** Run: `cd backend && .venv/bin/pytest tests/integration/test_isolation.py -v`
Expected: All pass (if Tasks 11-15 are done correctly).

**Step 3:** Commit:
```bash
git add backend/tests/integration/test_isolation.py
git commit -m "test: add cross-user data isolation integration tests"
```

---

## Task 17: Update main.py to pass current_user to all routers

**Files:** Modify `backend/app/main.py`

**Step 1:** Update the `create_app` function so all `build_xxx_router` calls receive `current_user`:
```python
app.include_router(build_inventory_router(get_session, current_user), prefix="/api")
app.include_router(build_rescue_router(get_session, recipe_adapters, current_user), prefix="/api")
app.include_router(build_recipe_router(get_session, current_user), prefix="/api")
app.include_router(build_history_router(get_session, current_user), prefix="/api")
```

**Step 2:** Run: `cd backend && .venv/bin/pytest -q`
Expected: All passing (auth tests, refactored tests, isolation tests).

**Step 3:** Run: `cd backend && .venv/bin/ruff check app tests && .venv/bin/mypy app`
Expected: Clean.

**Step 4:** Commit:
```bash
git add backend/app/main.py
git commit -m "feat: wire current_user into all protected routers"
```

---

## Task 18: Add .env.example entries

**Files:** Modify `.env.example`

**Step 1:** Add the three new environment variables to `.env.example`:
```bash
# Auth (required for multi-user mode)
FRIDGE_PAL_JWT_SECRET=change-me-to-a-random-string-at-least-32-characters-long
FRIDGE_PAL_DEMO_PASSWORD=demo12345
FRIDGE_PAL_COOKIE_SECURE=false
```

**Step 2:** Run: `docker compose --env-file .env.example config --quiet`
Expected: No errors.

**Step 3:** Commit:
```bash
git add .env.example
git commit -m "chore: add auth env vars to .env.example"
```

---

## Task 19: Frontend — add auth API client

**Files:** Create `frontend/src/api/auth.ts`

**Step 1:** Create `frontend/src/api/auth.ts`:
```typescript
export interface AuthUser {
  username: string
  isDemo: boolean
}

export async function register(username: string, password: string): Promise<AuthUser> {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: 'Registration failed' }))
    throw new Error(detail.detail)
  }
  return res.json()
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(detail.detail)
  }
  return res.json()
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const res = await fetch('/api/auth/me', { credentials: 'include' })
  if (res.status === 401) return null
  if (!res.ok) throw new Error('Failed to fetch user')
  return res.json()
}
```

**Step 2:** Run: `cd frontend && npm run typecheck`
Expected: Clean.

**Step 3:** Commit:
```bash
git add frontend/src/api/auth.ts
git commit -m "feat: add frontend auth API client"
```

---

## Task 20: Frontend — add auth store (composable)

**Files:** Create `frontend/src/features/auth/authStore.ts`

**Step 1:** Create `frontend/src/features/auth/authStore.ts`:
```typescript
import { ref, computed } from 'vue'
import { fetchCurrentUser, login as apiLogin, logout as apiLogout, register as apiRegister } from '../../api/auth'
import type { AuthUser } from '../../api/auth'

const currentUser = ref<AuthUser | null>(null)
const loading = ref(false)

export function useAuth() {
  const isAuthenticated = computed(() => currentUser.value !== null)

  async function init() {
    loading.value = true
    try {
      currentUser.value = await fetchCurrentUser()
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    currentUser.value = await apiLogin(username, password)
  }

  async function register(username: string, password: string) {
    currentUser.value = await apiRegister(username, password)
  }

  async function logout() {
    await apiLogout()
    currentUser.value = null
  }

  return { currentUser, isAuthenticated, loading, init, login, register, logout }
}
```

**Step 2:** Run: `cd frontend && npm run typecheck`
Expected: Clean.

**Step 3:** Commit:
```bash
git add frontend/src/features/auth/authStore.ts
git commit -m "feat: add frontend auth store composable"
```

---

## Task 21: Frontend — add Login and Register views

**Files:** Create `frontend/src/views/LoginView.vue`, `frontend/src/views/RegisterView.vue`

**Step 1:** Create `frontend/src/views/LoginView.vue` — a simple form with username, password, submit button, error message display, and a link to Register. Uses `useAuth().login()`. On success, `router.push('/')`.

**Step 2:** Create `frontend/src/views/RegisterView.vue` — same pattern with `useAuth().register()`. Shows validation errors from the API.

**Step 3:** Run: `cd frontend && npm run lint && npm run typecheck`
Expected: Clean.

**Step 4:** Commit:
```bash
git add frontend/src/views/LoginView.vue frontend/src/views/RegisterView.vue
git commit -m "feat: add Login and Register views"
```

---

## Task 22: Frontend — add router guard + routes

**Files:** Modify `frontend/src/router.ts`

**Step 1:** Add login and register routes, plus a global `beforeEach` guard:
```typescript
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import { useAuth } from './features/auth/authStore'

// Add to routes array:
{ path: '/login', name: 'login', component: LoginView, meta: { public: true } },
{ path: '/register', name: 'register', component: RegisterView, meta: { public: true } },

// Add guard before export:
router.beforeEach(async (to) => {
  const { isAuthenticated, init, loading } = useAuth()
  if (!loading.value && !isAuthenticated.value) {
    await init()
  }
  if (!isAuthenticated.value && !to.meta.public) {
    return { name: 'login' }
  }
})
```

**Step 2:** Run: `cd frontend && npm run typecheck`
Expected: Clean.

**Step 3:** Commit:
```bash
git add frontend/src/router.ts
git commit -m "feat: add auth routes and navigation guard"
```

---

## Task 23: Frontend — add user widget to App.vue

**Files:** Modify `frontend/src/App.vue`

**Step 1:** In `App.vue`, add a user widget to the top navigation bar showing the current username and a logout button. Use `useAuth()`. On logout, `router.push('/login')`. Hide the widget on `meta.public` routes.

**Step 2:** Call `useAuth().init()` in the `onMounted` hook of `App.vue` so the auth state is initialized on page load.

**Step 3:** Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: All clean.

**Step 4:** Commit:
```bash
git add frontend/src/App.vue
git commit -m "feat: add user widget and logout to App header"
```

---

## Task 24: Frontend — add credentials: 'include' to existing API clients

**Files:** Modify `frontend/src/api/inventory.ts`, `frontend/src/api/rescue.ts`, `frontend/src/api/recipes.ts`, `frontend/src/api/history.ts`

**Step 1:** In each of the 4 API client files, every `fetch(...)` call gains `credentials: 'include'`. Search for `fetch(` and add `credentials: 'include'` to the options object of each call.

**Step 2:** Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Expected: All clean.

**Step 3:** Commit:
```bash
git add frontend/src/api/
git commit -m "feat: include credentials in all API client fetch calls"
```

---

## Task 25: Update documentation

**Files:** Modify `AGENTS.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/DEPLOYMENT.md`, `README.md`, `docs/DOMAIN_AND_AI_CONTRACTS.md`

**Step 1 — AGENTS.md:**
- Decision Gates: change "The application has no authentication..." to reflect multi-user auth mode.
- Non-Negotiable Product Invariants: update the no-auth invariant to "User data is isolated by `user_id`; cross-user access returns 404."

**Step 2 — docs/PRODUCT_REQUIREMENTS.md:**
- OQ-03: change to "Resolved: protected external exposure with application-level authentication and per-user data isolation."
- FR-DEP-002: rewrite to "The application supports username/password authentication. JWT cookies manage sessions. Public deployment requires `FRIDGE_PAL_JWT_SECRET` and `FRIDGE_PAL_DEMO_PASSWORD` to be set."
- Non-Goals: remove "Accounts, shared households, and permissions."

**Step 3 — docs/IMPLEMENTATION_PLAN.md:**
- Tech Stack paragraph: update "OQ-03 is resolved: private-network..." to "OQ-03 is resolved: protected external exposure with auth."

**Step 4 — docs/DEPLOYMENT.md:**
- Update the security boundary section: "Fridge Pal supports username/password authentication. Public deployment requires setting `FRIDGE_PAL_JWT_SECRET` (>= 32 chars), `FRIDGE_PAL_DEMO_PASSWORD`, and `FRIDGE_PAL_COOKIE_SECURE=true`."
- Add the three env vars to the environment variable table.

**Step 5 — README.md:**
- Security boundary paragraph: rewrite to reflect auth is now supported.
- Environment variable table: add the three new variables.
- MVP Non-Goals: remove "Public accounts, authentication, or multi-user household collaboration."

**Step 6 — docs/DOMAIN_AND_AI_CONTRACTS.md:**
- Add invariant: "User-owned data (inventory, rescue sessions, recipes, history) is isolated by `user_id`. Every repository query filters by `user_id`. Cross-user access returns 404."

**Step 7:** Commit:
```bash
git add AGENTS.md docs/ README.md
git commit -m "docs: update canonical docs for multi-user auth mode"
```

---

## Task 26: Final verification

**Step 1:** Run backend full suite:
```bash
cd backend && .venv/bin/pytest -q && .venv/bin/ruff check app tests && .venv/bin/mypy app
```
Expected: All pass, ruff clean, mypy clean.

**Step 2:** Run frontend full suite:
```bash
cd frontend && npm run lint && npm run typecheck && npm run build
```
Expected: All clean.

**Step 3:** Run Docker config check:
```bash
docker compose --env-file .env.example config --quiet
```
Expected: No errors.

**Step 4:** Manual smoke test (optional):
- Start backend + frontend locally.
- Register a new user → verify demo data appears.
- Logout → login as `demo` → verify different lot IDs.
- Open a second browser, register another user → verify no data leak.

**Step 5:** Final commit if any fixups were made.

---

## Execution Notes

- **Task ordering matters.** Tasks 1-9 build the auth foundation. Tasks 10-17 retrofit user isolation into existing services and routers — these will temporarily break existing tests until each router is wired. Task 16 (isolation test) is the critical safety gate.
- **Existing test refactoring** (Tasks 12-15) is the most tedious part. The `authed_client` fixture pattern is key — every test that previously called the API directly must now register a user first and send the cookie.
- **The `_ensure_columns` function** in `session.py` must handle the case where an existing database is upgraded (adds nullable `user_id`, clears existing rows, then alters to NOT NULL). For fresh databases, `create_all` handles everything.
- **Idempotency keys** in `demo_seed.py` must include `user_id` to avoid collisions when multiple users have demo data.

