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
