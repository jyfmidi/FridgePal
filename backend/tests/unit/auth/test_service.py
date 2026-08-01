import app.auth.service as service
import pytest
from app.auth.service import (
    LoginError,
    RegisterError,
    authenticate_user,
    create_user,
    get_user_by_id,
)
from app.infrastructure.db.session import create_database
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


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


def test_create_user_duplicate_survives_commit_conflict(session: Session, monkeypatch):
    """A unique-constraint race must surface as RegisterError, not IntegrityError."""

    def conflicting_commit() -> None:
        raise IntegrityError("INSERT INTO users", {}, Exception("duplicate username"))

    monkeypatch.setattr(session, "commit", conflicting_commit)
    with pytest.raises(RegisterError) as exc:
        create_user(session, "alice", "password123")
    assert exc.value.code == "AUTH_USERNAME_TAKEN"


def test_create_user_rejects_passwords_over_72_bytes(session: Session):
    """bcrypt only reads the first 72 bytes; longer inputs must be rejected up front."""
    with pytest.raises(RegisterError) as exc:
        create_user(session, "alice", "p" * 73)
    assert exc.value.code == "AUTH_PASSWORD_TOO_LONG"


def test_authenticate_unknown_user_still_compares_a_dummy_hash(session: Session, monkeypatch):
    """Unknown-user logins run one bcrypt comparison to avoid username timing leaks."""
    from app.auth.password import verify_password

    compared: list[str] = []
    real = verify_password
    monkeypatch.setattr(
        service,
        "verify_password",
        lambda plain, hashed: (compared.append(hashed), real(plain, hashed))[1],
    )
    with pytest.raises(LoginError):
        service.authenticate_user(session, "ghost", "password123")
    assert compared == [service._DUMMY_HASH]
