"""
services/account_service.py
---------------------------------------
Account Service (password reset + email verification)
MoodFlix AI
"""

from database.repositories import user_repo, token_repo
from database.token_model import create_reset_token, create_verify_token
from database.ids import parse_id
from services.auth_service import hash_password, validate_password
from services.email_service import send_password_reset_email, send_verification_email
from utils.logger import get_logger

log = get_logger("account_service")


# ==========================================
# Password Reset
# ==========================================

def request_password_reset(email: str, base_url: str):
    """
    Always looks like it succeeded to the caller, whether or not the
    email exists — this avoids leaking which emails have accounts.
    """

    user = user_repo.find_by_email(email)

    if not user:
        log.info(f"Password reset requested for unknown email: {email}")
        return

    raw_token, token_doc = create_reset_token(str(user["_id"]))
    token_repo.insert_one(token_doc)

    reset_url = f"{base_url.rstrip('/')}/reset-password?token={raw_token}"
    send_password_reset_email(user["email"], user.get("name", ""), reset_url)


def reset_password(raw_token: str, new_password: str):
    """Returns (ok: bool, error_message)."""

    token_doc = token_repo.find_valid(raw_token, "password_reset")
    if not token_doc:
        return False, "This reset link is invalid or has expired. Please request a new one."

    ok, message = validate_password(new_password)
    if not ok:
        return False, message

    user_repo.update_one(
        {"_id": parse_id(token_doc["user_id"])},
        {"$set": {"password": hash_password(new_password), "failed_login_attempts": 0, "locked_until": None}},
    )
    token_repo.mark_used(token_doc["_id"])

    log.info(f"Password reset completed for user={token_doc['user_id']}")

    return True, None


# ==========================================
# Email Verification
# ==========================================

def send_verification(user: dict, base_url: str):
    raw_token, token_doc = create_verify_token(str(user["_id"]))
    token_repo.insert_one(token_doc)

    verify_url = f"{base_url.rstrip('/')}/verify-email?token={raw_token}"
    send_verification_email(user["email"], user.get("name", ""), verify_url)


def verify_email(raw_token: str):
    """Returns (ok: bool, error_message)."""

    token_doc = token_repo.find_valid(raw_token, "email_verify")
    if not token_doc:
        return False, "This verification link is invalid or has expired."

    user_repo.update_one(
        {"_id": parse_id(token_doc["user_id"])},
        {"$set": {"is_verified": True}},
    )
    token_repo.mark_used(token_doc["_id"])

    log.info(f"Email verified for user={token_doc['user_id']}")

    return True, None
