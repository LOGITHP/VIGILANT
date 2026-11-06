import pytest
from datetime import timedelta
import jwt
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token
)
from app.core.config import settings


def test_argon2id_password_hashing():
    raw_password = "SecurePassword123!"
    hashed = hash_password(raw_password)

    # Argon2id hashes start with $argon2id$
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_access_token_creation_and_decoding():
    data = {"sub": "123e4567-e89b-12d3-a456-426614174000", "email": "test@vigilant.ai", "roles": ["OPERATOR"]}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=10))

    payload = decode_token(token)
    assert payload["sub"] == data["sub"]
    assert payload["email"] == data["email"]
    assert payload["roles"] == ["OPERATOR"]
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_creation_and_decoding():
    data = {"sub": "user_123", "session_id": "sess_456"}
    token = create_refresh_token(data=data, expires_delta=timedelta(days=7))

    payload = decode_token(token)
    assert payload["sub"] == "user_123"
    assert payload["session_id"] == "sess_456"
    assert payload["type"] == "refresh"


def test_expired_token_handling():
    data = {"sub": "user_123"}
    # Token expired 1 minute ago
    token = create_access_token(data=data, expires_delta=timedelta(minutes=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_token_hash_deterministic():
    token = "some-long-jwt-string-sample"
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest length
