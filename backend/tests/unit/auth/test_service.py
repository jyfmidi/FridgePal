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
