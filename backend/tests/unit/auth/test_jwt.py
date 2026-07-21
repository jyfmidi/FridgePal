from datetime import timedelta

import pytest
from app.auth.jwt import TokenError, decode_token, encode_token


def test_encode_decode_roundtrip():
    token = encode_token("user-123", "alice", is_demo=False)
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["username"] == "alice"
    assert payload["is_demo"] is False


def test_decode_invalid_token_raises():
    with pytest.raises(TokenError):
        decode_token("not-a-jwt")


def test_decode_expired_token_raises():
    token = encode_token("user-123", "alice", is_demo=False, expires_in=timedelta(seconds=-1))
    with pytest.raises(TokenError):
        decode_token(token)
