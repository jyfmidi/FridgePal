from app.main import create_app
from fastapi.testclient import TestClient


def _client() -> TestClient:
    from app.config import get_settings

    get_settings.cache_clear()
    import os

    os.environ["DATABASE_URL"] = (
        f"sqlite:///file:test_auth_{__import__('uuid').uuid4().hex}?mode=memory&cache=shared&uri=true"
    )
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
    assert r.json()["detail"] == "AUTH_USERNAME_TAKEN"


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
    assert r.json()["detail"] == "AUTH_INVALID_CREDENTIALS"


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


def test_login_rate_limit_returns_429(monkeypatch):
    monkeypatch.setenv("AUTH_LOGIN_RATE_PER_MINUTE", "2")
    c = _client()
    c.post("/api/auth/register", json={"username": "eve", "password": "password123"})
    c.cookies.clear()
    for _ in range(2):
        r = c.post("/api/auth/login", json={"username": "eve", "password": "password123"})
        assert r.status_code == 200
    r = c.post("/api/auth/login", json={"username": "eve", "password": "password123"})
    assert r.status_code == 429
    assert r.json()["detail"] == "AUTH_RATE_LIMITED"


def test_seed_demo_data_false_skips_demo_user_and_register_seed(monkeypatch):
    monkeypatch.setenv("SEED_DEMO_DATA", "false")
    c = _client()
    # The built-in demo account is not created.
    r = c.post("/api/auth/login", json={"username": "demo", "password": "demo-pass-123"})
    assert r.status_code == 401
    # A freshly registered user receives no demo inventory.
    c.post("/api/auth/register", json={"username": "fresh", "password": "password123"})
    r = c.get("/api/storage")
    assert r.status_code == 200
    body = r.json()
    assert body["inventory"] == []
    assert body["useSoon"] == []
