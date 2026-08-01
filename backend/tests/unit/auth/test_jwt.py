from datetime import timedelta

import jwt as pyjwt
import pytest
from app.auth.jwt import JWT_AUDIENCE, JWT_ISSUER, TokenError, decode_token, encode_token
from app.config import get_settings


def test_encode_decode_roundtrip():
    token = encode_token("user-123", "alice", is_demo=False)
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["username"] == "alice"
    assert payload["is_demo"] is False
    assert payload["iss"] == JWT_ISSUER
    assert payload["aud"] == JWT_AUDIENCE


def test_decode_invalid_token_raises():
    with pytest.raises(TokenError):
        decode_token("not-a-jwt")


def test_decode_expired_token_raises():
    token = encode_token("user-123", "alice", is_demo=False, expires_in=timedelta(seconds=-1))
    with pytest.raises(TokenError):
        decode_token(token)


def test_decode_rejects_token_without_audience():
    """Tokens minted before the issuer/audience claims must not verify."""
    raw = pyjwt.encode({"sub": "user-123"}, get_settings().jwt_secret, algorithm="HS256")
    with pytest.raises(TokenError):
        decode_token(raw)
