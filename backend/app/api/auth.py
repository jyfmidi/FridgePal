"""HTTP boundary for authentication endpoints."""

import re
from typing import Annotated

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
    session_provider,
    session_factory: sessionmaker[Session],
    current_user: callable,
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
