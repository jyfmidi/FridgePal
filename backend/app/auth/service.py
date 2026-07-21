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
