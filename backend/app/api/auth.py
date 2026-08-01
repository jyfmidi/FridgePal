"""HTTP boundary for authentication endpoints."""

import re
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session, sessionmaker

from app.auth.dependencies import (
    clear_session_cookie,
    set_session_cookie,
)
from app.auth.jwt import encode_token
from app.auth.rate_limit import RateLimiter
from app.auth.service import (
    LoginError,
    RegisterError,
    UserContext,
    authenticate_user,
    create_user,
)
from app.config import get_settings
from app.infrastructure.db.demo_seed import seed_demo_inventory_for_user
from app.infrastructure.db.models import UserRow

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_pattern(cls, value: str) -> str:
        if not USERNAME_PATTERN.match(value):
            raise ValueError(
                "Username may only contain letters, numbers, underscores, and hyphens."
            )
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)

    username: str
    is_demo: bool
    is_admin: bool = False


def _user_response(user: UserContext | UserRow) -> UserResponse:
    return UserResponse(
        username=user.username,
        is_demo=user.is_demo,
        is_admin=user.is_admin,
    )


def _rate_limit_dependency(limiter: RateLimiter, key_prefix: str):
    """Build a FastAPI dependency that rejects attempts beyond the limiter budget."""

    def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        if not limiter.allow(f"{key_prefix}:{client}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AUTH_RATE_LIMITED",
            )

    return dependency


def build_auth_router(
    session_provider,
    session_factory: sessionmaker[Session],
    current_user: Callable[..., UserContext],
    *,
    seed_on_register: bool = True,
) -> APIRouter:
    api = APIRouter()
    settings = get_settings()
    login_limit = _rate_limit_dependency(
        RateLimiter(settings.auth_login_rate_per_minute, 60.0), "login"
    )
    register_limit = _rate_limit_dependency(
        RateLimiter(settings.auth_register_rate_per_minute, 60.0), "register"
    )

    @api.post(
        "/auth/register",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(register_limit)],
    )
    def register(
        payload: RegisterRequest,
        response: Response,
        session: Annotated[Session, Depends(session_provider)],
    ) -> UserResponse:
        try:
            user = create_user(session, payload.username, payload.password)
        except RegisterError as error:
            conflict = error.code == "AUTH_USERNAME_TAKEN"
            code = status.HTTP_409_CONFLICT if conflict else status.HTTP_422_UNPROCESSABLE_ENTITY
            raise HTTPException(status_code=code, detail=error.code) from error
        if seed_on_register:
            seed_demo_inventory_for_user(session_factory, user.id)
        token = encode_token(user.id, user.username, is_demo=user.is_demo, is_admin=user.is_admin)
        set_session_cookie(response, token)
        return _user_response(user)

    @api.post("/auth/login", dependencies=[Depends(login_limit)])
    def login(
        payload: LoginRequest,
        response: Response,
        session: Annotated[Session, Depends(session_provider)],
    ) -> UserResponse:
        try:
            ctx = authenticate_user(session, payload.username, payload.password)
        except LoginError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH_INVALID_CREDENTIALS"
            ) from error
        token = encode_token(ctx.user_id, ctx.username, is_demo=ctx.is_demo, is_admin=ctx.is_admin)
        set_session_cookie(response, token)
        return _user_response(ctx)

    @api.post("/auth/logout")
    def logout(response: Response) -> dict[str, str]:
        clear_session_cookie(response)
        return {"status": "ok"}

    @api.get("/auth/me")
    def me(user: Annotated[UserContext, Depends(current_user)]) -> UserResponse:
        return _user_response(user)

    return api
