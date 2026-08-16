"""
services/auth_service.py
---------------------------------------
Authentication Service
MoodFlix AI
"""

from datetime import datetime, timedelta

import bcrypt
from email_validator import validate_email as _validate_email, EmailNotValidError

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


# ==========================================
# Password Hashing
# ==========================================

def hash_password(password: str) -> str:
    """
    Convert a plain password into a secure hash.
    """

    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


# ==========================================
# Verify Password
# ==========================================

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a user's password.
    """

    if not password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed hash (shouldn't happen, but don't 500 on it).
        return False


# ==========================================
# Validate Email
# ==========================================

def validate_email(email: str) -> bool:

    if not email:
        return False

    try:
        # check_deliverability=False: we don't want to make a live DNS/MX
        # lookup on every signup attempt (slow, and fails offline).
        _validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


# ==========================================
# Validate Password
# ==========================================

COMMON_WEAK_PASSWORDS = {
    "password", "password1", "12345678", "qwerty123", "letmein123", "welcome123",
}


def validate_password(password: str):

    """
    Returns:
    (True, "")

    OR

    (False, "Reason")
    """

    if not password or len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not any(c.isupper() for c in password):
        return False, "Password must contain one uppercase letter."

    if not any(c.islower() for c in password):
        return False, "Password must contain one lowercase letter."

    if not any(c.isdigit() for c in password):
        return False, "Password must contain one number."

    if password.lower() in COMMON_WEAK_PASSWORDS:
        return False, "That password is too common. Please choose something more unique."

    return True, ""


# ==========================================
# Account Lockout (brute-force protection)
# ==========================================

def is_locked(user: dict) -> bool:
    locked_until = user.get("locked_until")
    return bool(locked_until and locked_until > datetime.utcnow())


def record_failed_login(user: dict) -> dict:
    """Returns the $set update to apply after a failed login attempt."""

    attempts = user.get("failed_login_attempts", 0) + 1
    update = {"failed_login_attempts": attempts}

    if attempts >= MAX_FAILED_ATTEMPTS:
        update["locked_until"] = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)

    return update


def record_successful_login() -> dict:
    """Returns the $set update to apply after a successful login."""

    return {"failed_login_attempts": 0, "locked_until": None}
