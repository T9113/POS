import hashlib
import os
import secrets

def hash_password(password: str, salt: str = None) -> str:
    """Hash password using SHA-256 with cryptographic salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored salted hash against a user-provided password."""
    if not stored_password:
        return False
    # Support legacy or unhashed dev passwords if any
    if "$" not in stored_password:
        return stored_password == provided_password
    
    salt, hash_val = stored_password.split("$", 1)
    recalculated = hashlib.sha256((salt + provided_password).encode("utf-8")).hexdigest()
    return recalculated == hash_val
