"""
database/token_model.py
---------------------------------------
Token Model
MoodFlix AI

Single-use, expiring tokens for password reset and email verification.
Only a SHA-256 hash of the token is stored — the raw token exists only
in the emailed link, never at rest, so a database read alone can't be
used to reset someone's password.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

RESET_TOKEN_TTL_MINUTES = 30
VERIFY_TOKEN_TTL_HOURS = 24


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_token(user_id: str, purpose: str, ttl: timedelta):
    """
    purpose: "password_reset" | "email_verify"
    Returns (raw_token, token_doc). Give raw_token to the user (via
    email); store token_doc.
    """

    raw_token = secrets.token_urlsafe(32)

    doc = {
        "user_id": user_id,
        "purpose": purpose,
        "token_hash": _hash(raw_token),
        "expires_at": datetime.utcnow() + ttl,
        "used": False,
        "created_at": datetime.utcnow(),
    }

    return raw_token, doc


def create_reset_token(user_id: str):
    return create_token(user_id, "password_reset", timedelta(minutes=RESET_TOKEN_TTL_MINUTES))


def create_verify_token(user_id: str):
    return create_token(user_id, "email_verify", timedelta(hours=VERIFY_TOKEN_TTL_HOURS))


def find_valid_token(tokens_collection, raw_token: str, purpose: str):
    """Look up a non-expired, unused token document by its raw value."""

    token_hash = _hash(raw_token)
    doc = tokens_collection.find_one({"token_hash": token_hash, "purpose": purpose})

    if not doc:
        return None
    if doc.get("used"):
        return None
    if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
        return None

    return doc
