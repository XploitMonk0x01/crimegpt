"""
Password hashing (bcrypt) and file integrity (SHA-256) utilities.

Usage:
    from app.utils.hashing import hash_password, verify_password, sha256_hash

    hashed = hash_password("secret_pin")
    assert verify_password("secret_pin", hashed) is True

    file_hash = sha256_hash(file_bytes)
"""

import hashlib

from passlib.context import CryptContext

# bcrypt context — always use this, never raw hashlib for passwords
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes (for evidence integrity)."""
    return hashlib.sha256(data).hexdigest()
