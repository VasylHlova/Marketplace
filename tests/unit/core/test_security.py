import hashlib
import time
from datetime import timedelta

import jwt

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hash_is_not_plaintext():
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert hashed != password


def test_password_hash_is_bcrypt_format():
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert hashed.startswith("$2b$"), "Expected bcrypt hash starting with $2b$"


def test_verify_password_correct():
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True


def test_verify_password_wrong():
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert verify_password("wrong_password", hashed) is False


def test_verify_password_returns_bool():
    password = "check_type"
    hashed = get_password_hash(password)
    result = verify_password(password, hashed)
    assert isinstance(result, bool), f"Expected bool, got {type(result)}"


def test_no_sha256_prehash():
    password = "raw_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    sha256_hex = hashlib.sha256(password.encode()).hexdigest()
    assert verify_password(sha256_hex, hashed) is False, (
        "SHA-256 pre-hash anti-pattern detected: sha256(password) verifies against hash"
    )


def test_create_access_token():
    token = create_access_token("user_123", timedelta(minutes=15))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "user_123"
    assert "exp" in decoded


def test_create_access_token_expiry():
    token = create_access_token("user_abc", timedelta(minutes=5))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert abs(decoded["exp"] - (time.time() + 300)) < 10
