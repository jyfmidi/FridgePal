import pytest
from app.auth.dependencies import current_user_factory
from app.auth.jwt import encode_token
from app.auth.service import create_user
from app.infrastructure.db.session import create_database
from fastapi import HTTPException
from starlette.requests import Request


@pytest.fixture()
def deps():
    _, factory = create_database("sqlite:///:memory:")
    with factory() as session:
        user = create_user(session, "alice", "password123")
        yield session, user, current_user_factory(factory)


def test_current_user_valid_cookie(deps):
    _, user, current_user = deps
    token = encode_token(user.id, user.username, is_demo=False)
    cookie = f"fp_session={token}".encode()
    request = Request(scope={"type": "http", "headers": [(b"cookie", cookie)]})
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
    cookie = f"fp_session={token}".encode()
    request = Request(scope={"type": "http", "headers": [(b"cookie", cookie)]})
    with pytest.raises(HTTPException) as exc:
        current_user(request)
    assert exc.value.status_code == 401
