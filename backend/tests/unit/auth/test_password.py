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
