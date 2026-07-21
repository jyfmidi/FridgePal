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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        try:
            payload = decode_token(token)
        except TokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
            ) from exc
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
